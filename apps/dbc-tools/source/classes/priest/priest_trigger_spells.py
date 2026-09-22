"""
Priest - spells that are never directly cast - proc/periodic-tick effects, trigger_spell targets, hidden talent-rank buffs, etc..

Split from a single source/classes/priest.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .priest_...` below) resolve.
"""

from lib.dsl import ApplyAura, AuraType, DispelType, Effect, EffectType, Mechanic, School, SpellModOp
from lib.dsl.registry import bonus_coefficients, procs_on, scripted_by, spell
from . import _masks

# Proc flags/phases used by the procs_on() calls below - src/server/game/Spells/SpellMgr.h's
# ProcFlags / ProcFlagsSpellPhase / ProcAttributes enums. Named here rather than as bare ints so a
# reader doesn't have to decode a hex literal to see what a talent procs off.
PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS = 0x00004000
PROC_FLAG_TAKEN_DAMAGE = 0x00100000
PROC_SPELL_PHASE_CAST = 0x1
PROC_SPELL_PHASE_HIT = 0x2
PROC_ATTR_TRIGGERED_CAN_PROC = 0x2
# Priest Holy rework (priest-rework.HOLY.md) additions - same source, SpellMgr.h.
PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG = 0x00010000
PROC_FLAG_TAKEN_SPELL_MAGIC_DMG_CLASS_NEG = 0x00020000
PROC_FLAG_DONE_PERIODIC = 0x00040000
PROC_FLAG_TAKEN_PERIODIC = 0x00080000
PROC_SPELL_TYPE_DAMAGE = 0x0000001
PROC_SPELL_TYPE_HEAL = 0x0000002
PROC_HIT_CRITICAL = 0x0000002


lightwell_renew_7001 = spell(
    id=7001,
    name='Lightwell Renew',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=262144,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=266, points_per_level=13.3, implicit_target_a=21, apply_aura=AuraType.PERIODIC_HEAL, amplitude=2000),
    ],
    spell_icon_id=1878,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 40); RealPointsPerLevel from rank1→level-60 slope (anchor rank 27874, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (48085, rank 6); MaxLevel set to 80',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx3': 128, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Restore $s1 health every $t1 sec.', 'BaseLevel': 40, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Restore $s1 health every $t1 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 1188520, 'SpellClassMask_3': 16384, 'SpellClassSet': 6, 'SpellLevel': 40, 'SpellVisualID_1': 7551},
)


focused_casting_14743 = spell(
    id=14743,
    name='Focused Casting',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=108, misc_value=9),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, points_per_level=-0.1667, implicit_target_a=1, apply_aura=232, misc_value=26),
    ],
    spell_icon_id=1499,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1→level-60 slope (anchor rank 27828, rank 2); coefficient/cast_time_ms/mana_cost_pct from max rank (27828, rank 2); MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Cannot lose casting time from taking damage while casting Priest spells and decreases the duration of Interrupt effects by $s2%.', 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When cast, you no longer lose casting time due to taking damage.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1144405648, 'EffectSpellClassMaskA_2': 1156, 'EffectSpellClassMaskA_3': 64, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 4096, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellVisualID_1': 7645},
)


inspiration_14893 = spell(
    id=14893,
    name='Inspiration',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-4, points_per_level=-0.1167, implicit_target_a=21, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=1),
    ],
    spell_icon_id=1463,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1→level-60 slope (anchor rank 15359, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (15359, rank 3); MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Reduces physical damage taken by $s1%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces your target's physical damage taken by $s1% for $14893d after getting a critical effect from your Flash Heal, Heal, Greater Heal, Binding Heal, Penance, Prayer of Mending, Prayer of Healing, or Circle of Healing spell.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassMask_2': 4096, 'SpellClassSet': 6},
)


holy_nova_23455 = spell(
    id=23455,
    name='Holy Nova',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=51, points_per_level=6.25, die_sides=9, implicit_target_a=20, radius_yards=10.0),
    ],
    spell_icon_id=1874,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1→level-60 slope (anchor rank 27805, rank 6); coefficient/cast_time_ms/mana_cost_pct from max rank (48076, rank 9); MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes an explosion of holy light around the caster, causing $15237s1 Holy damage to all enemy targets within $15237a1 yards and healing all party members within $23455a1 yards for $23455s1.  These effects cause no threat.', 'EffectBonusMultiplier_1': 0.30300000309944153, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassMask_1': 134217728, 'SpellClassSet': 6, 'SpellLevel': 20, 'SpellVisualID_1': 6882},
)


blessed_recovery_27813 = spell(
    id=27813,
    name='Blessed Recovery',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=16842752,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PERIODIC_HEAL, amplitude=2000),
    ],
    spell_icon_id=1875,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1→level-60 slope (anchor rank 27818, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (27818, rank 3); MaxLevel set to 80',
    raw_overrides={'AttributesEx4': 524416, 'AttributesEx5': 8, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Heals $27811s1% of damage from a recent crit over $d.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals the target over $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 1073741824, 'SpellClassMask_2': 4096, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellVisualID_1': 7548, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


misery_33196 = spell(
    id=33196,
    name='Misery',
    school=School.SHADOW,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    duration_ms=24000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, points_per_level=0.0333, implicit_target_a=6, apply_aura=186, misc_value=127),
    ],
    spell_icon_id=2211,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1→level-60 slope (anchor rank 33198, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (33198, rank 3); MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 4, 'AttributesEx3': 196608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Chance to hit with spells on the target increased by $s1%.', 'AuraInterruptFlags': 524288, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Shadow Word: Pain, Mind Flay and Vampiric Touch spells also increase the chance for harmful spells to hit by $33196s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 32, 'EffectSpellClassMaskB_1': 32, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassSet': 6},
)


prayer_of_mending_41635 = spell(
    id=41635,
    name='Prayer of Mending',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=57, apply_aura=225, radius_yards=20.0),
    ],
    spell_icon_id=2219,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 68); RealPointsPerLevel from rank1→top rank's own top level (83, chain has a gap at 60) slope (anchor rank 48111, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (48111, rank 3); MaxLevel set to 80",
    raw_overrides={'AttributesEx': 1024, 'AttributesEx2': 524292, 'AttributesEx3': 1140850688, 'AttributesEx4': 524288, 'AttributesEx5': 32, 'AttributesEx6': 67108864, 'AttributesEx7': 1073741824, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Heals for $33076s1 the next time you take damage.', 'AuraInterruptFlags': 524288, 'BaseLevel': 68, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Places a spell on the target that heals them the next time they take damage.  When the heal occurs, Prayer of Mending jumps to a party or raid member within $a1 yards.  Jumps up to $n times and lasts $d after each jump.  This spell can only be placed on one target at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 5, 'ProcTypeMask': 697000, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_2': 32, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 68, 'SpellVisualID_1': 8070, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


focused_will_45237 = spell(
    id=45237,
    name='Focused Will',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=16777216,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-3, points_per_level=-0.0333, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=2, points_per_level=0.0333, implicit_target_a=1, apply_aura=AuraType.MOD_HEALING_PCT, misc_value=127),
    ],
    spell_icon_id=2215,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1→level-60 slope (anchor rank 45242, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (45242, rank 3); MaxLevel set to 80',
    raw_overrides={'AttributesEx4': 524416, 'AttributesEx5': 8, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'All damage reduced by $s1%.  Healing effects increased by $s2%.', 'CastingTimeIndex': 1, 'CumulativeAura': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'After taking a critical hit you gain the Focused Will effect, reducing all damage taken by $s1% and increasing healing effects on you by $s2%.  Stacks up to $u times.  Lasts $d.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 1152794256, 'EffectSpellClassMaskA_2': 1156, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 4096, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellVisualID_1': 7645},
)


penance_47666 = spell(
    id=47666,
    name='Penance',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=239, points_per_level=5.625, implicit_target_a=77),
    ],
    spell_icon_id=2818,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 60); RealPointsPerLevel from rank1→top rank's own top level (84, chain has a gap at 60) slope (anchor rank 53000, rank 4); coefficient/cast_time_ms/mana_cost_pct from max rank (53000, rank 4); MaxLevel set to 80",
    raw_overrides={'AttributesEx2': 4, 'AttributesEx3': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Launches a volley of holy light at the target, causing $47666s1 Holy damage to an enemy, or $47750s1 healing to an ally instantly and every $47758t2 sec for $47758d.', 'EffectBonusMultiplier_1': 0.2290000021457672, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 40.0, 'SpellClassMask_2': 32768, 'SpellClassSet': 6, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 10982},
)


penance_47750 = spell(
    id=47750,
    name='Penance',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=669, points_per_level=33.9167, die_sides=87, implicit_target_a=77),
    ],
    spell_icon_id=2818,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 60); RealPointsPerLevel from rank1→top rank's own top level (84, chain has a gap at 60) slope (anchor rank 52985, rank 4); coefficient/cast_time_ms/mana_cost_pct from max rank (52985, rank 4); MaxLevel set to 80",
    raw_overrides={'AttributesEx2': 4194308, 'AttributesEx3': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Launches a volley of holy light at the target, causing $47666s1 Holy damage to an enemy, or $47750s1 healing to an ally instantly and every $47758t2 sec for $47758d.', 'EffectBonusMultiplier_1': 0.5370000004768372, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 40.0, 'SpellClassMask_2': 65536, 'SpellClassSet': 6, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 10981},
)


penance_47757 = spell(
    id=47757,
    name='Penance',
    school=School.HOLY,
    attributes=536936704,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=40.0,
    duration_ms=2000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=21, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, points_per_level=-0.0169, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=1000, trigger_spell=penance_47750.id),
    ],
    spell_icon_id=2818,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1→level-60 slope (anchor rank 52988, rank 4); coefficient/cast_time_ms/mana_cost_pct from max rank (52988, rank 4); MaxLevel set to 80',
    raw_overrides={'AttributesEx': 335561924, 'AttributesEx4': 134217728, 'AttributesEx5': 8704, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31756, 'Description_Lang_Mask': 16712190, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 65536, 'SpellClassMask_3': 128, 'SpellClassSet': 6, 'SpellLevel': 1, 'SpellPriority': 50, 'SpellVisualID_1': 10980},
)


penance_47758 = spell(
    id=47758,
    name='Penance',
    school=School.HOLY,
    attributes=536936704,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=2000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=1000, trigger_spell=penance_47666.id),
    ],
    spell_icon_id=2818,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1→level-60 slope (anchor rank 53003, rank 4); coefficient/cast_time_ms/mana_cost_pct from max rank (53003, rank 4); MaxLevel set to 80',
    raw_overrides={'AttributesEx': 335561860, 'AttributesEx4': 134217728, 'AttributesEx5': 8704, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31756, 'Description_Lang_Mask': 16712190, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_3': 128, 'SpellClassSet': 6, 'SpellLevel': 1, 'SpellPriority': 50, 'SpellVisualID_1': 10980},
)


improved_spirit_tap_49694 = spell(
    id=49694,
    name='Improved Spirit Tap',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    attributes=134283264,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, points_per_level=0.0833, implicit_target_a=1, apply_aura=137, misc_value=4),
        Effect(type=EffectType.APPLY_AURA, base_points=16, points_per_level=0.2667, implicit_target_a=1, apply_aura=134),
    ],
    spell_icon_id=152,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1→level-60 slope (anchor rank 59000, rank 2); coefficient/cast_time_ms/mana_cost_pct from max rank (59000, rank 2); MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Spirit increased $s1% and allows $s2% mana regeneration while casting.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Mind Blast and Shadow Word: Death critical strikes increase your total Spirit by $s1%. For the duration, your mana will regenerate at a $s2% rate while casting. Lasts $49694d.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 134217728, 'SpellClassMask_2': 4096, 'SpellClassMask_3': 1024, 'SpellClassSet': 6},
)


mind_sear_49821 = spell(
    id=49821,
    name='Mind Sear',
    school=School.SHADOW,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=182, points_per_level=3.2222, die_sides=15, implicit_target_a=76, implicit_target_b=16, radius_yards=10.0),
    ],
    spell_icon_id=2895,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 75); RealPointsPerLevel from rank1→top rank's own top level (84, chain has a gap at 60) slope (anchor rank 53022, rank 2); coefficient/cast_time_ms/mana_cost_pct from max rank (53022, rank 2); MaxLevel set to 80",
    raw_overrides={'AttributesEx': 136, 'AttributesEx2': 4194304, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Causing shadow damage to all targets within $a1 yards.', 'BaseLevel': 75, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes an explosion of shadow magic around the enemy target, causing $s1 Shadow damage every 1 sec for $48045d to all enemies within $a1 yards around the target.', 'EffectBonusMultiplier_1': 0.28600001335144043, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 524288, 'SpellClassSet': 6, 'SpellLevel': 75, 'SpellVisualID_1': 12122},
)


mental_agility_14520 = spell(
    id=14520,
    name='Mental Agility',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=157,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your instant cast spells by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2470560111, 'EffectSpellClassMaskA_2': 371, 'EffectSpellClassMaskA_3': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


silent_resolve_14523 = spell(
    id=14523,
    name='Silent Resolve',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-8, implicit_target_a=1, apply_aura=AuraType.MOD_THREAT, misc_value=66),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=28),
        Effect(type=EffectType.APPLY_AURA, base_points=-8, implicit_target_a=1, apply_aura=108, misc_value=2),
    ],
    spell_icon_id=338,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the threat generated by your Holy and Discipline spells by $s1% and reduces the chance your helpful spells and damage over time effects will be dispelled by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_3': 1024, 'EffectSpellClassMaskC_1': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


improved_inner_fire_14747 = spell(
    id=14747,
    name='Improved Inner Fire',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108, misc_value=8),
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=107, misc_value=4),
    ],
    spell_icon_id=51,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effect of your Inner Fire spell by $s1%, and increases the total number of charges by $s3.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 2, 'EffectSpellClassMaskB_1': 2, 'EffectSpellClassMaskC_1': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


# Priest Discipline rework (docs/reworks/priest-disc-rework.md (2,2)): amounts are unchanged
# (+5/10/15%, stored live-minus-1); rank 3 gains a second effect, a SPELL_AURA_DUMMY that marks the
# Mastery capstone for spell_pri_power_word_shield_aura::CalculateAmount and
# Priest::TryConvertHealToSpiritShell. WP-B keys that off HasAura(14769) rather than the
# marker-aura-by-icon idiom, because icon 566 (Spell_Holy_PowerWordShield) is NOT unique inside the
# priest family - Power Word: Shield 17, Reflective Shield 33201/33202 and the new Greater Power
# Word: Shield rows all use it too.
_IMPROVED_PWS_NOTE = (
    'Discipline rework (2,2): amounts unchanged; rank 3 gains a DUMMY effect marking the Mastery '
    'capstone (read by HasAura(14769), not by icon - icon 566 is shared).'
)


improved_power_word_shield_14748 = spell(
    id=14748,
    name='Improved Power Word: Shield',
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
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.ALL_EFFECTS),
    ],
    spell_icon_id=566,
    notes=_IMPROVED_PWS_NOTE,
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage absorbed by your Power Word: Shield by 5%.\n\n|cFF9D9D9DCapstone Bonus: Your Power Word: Shield and Spirit Shell absorption is additionally increased by your Mastery. This bonus is multiplicative and applies after all other modifiers.|r', 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 1, 'EffectSpellClassMaskA_1': _masks.PWS, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


improved_power_word_fortitude_14749 = spell(
    id=14749,
    name='Improved Power Word: Fortitude',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=137, misc_value=2),
    ],
    spell_icon_id=685,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effect of your Power Word: Fortitude and Prayer of Fortitude spells by $s1%, and increases your total Stamina by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


improved_mana_burn_14750 = spell(
    id=14750,
    name='Improved Mana Burn',
    school=School.NORMAL,
    attributes=448,
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
    spell_icon_id=212,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the casting time of your Mana Burn spell by $/1000;S1 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


improved_power_word_fortitude_14767 = spell(
    id=14767,
    name='Improved Power Word: Fortitude',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=137, misc_value=2),
    ],
    spell_icon_id=685,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effect of your Power Word: Fortitude and Prayer of Fortitude spells by $s1%, and increases your total Stamina by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


improved_power_word_shield_14768 = spell(
    id=14768,
    name='Improved Power Word: Shield',
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
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.ALL_EFFECTS),
    ],
    spell_icon_id=566,
    notes=_IMPROVED_PWS_NOTE,
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage absorbed by your Power Word: Shield by 10%.\n\n|cFF9D9D9DCapstone Bonus: Your Power Word: Shield and Spirit Shell absorption is additionally increased by your Mastery. This bonus is multiplicative and applies after all other modifiers.|r', 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 1, 'EffectSpellClassMaskA_1': _masks.PWS, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


improved_power_word_shield_14769 = spell(
    id=14769,
    name='Improved Power Word: Shield',
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
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.ALL_EFFECTS),
        ApplyAura(AuraType.DUMMY, base_points=0, implicit_target_a=1),
    ],
    spell_icon_id=566,
    notes=_IMPROVED_PWS_NOTE,
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage absorbed by your Power Word: Shield by 15%.\n\nCapstone Bonus: Your Power Word: Shield and Spirit Shell absorption is additionally increased by your Mastery. This bonus is multiplicative and applies after all other modifiers.', 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 1, 'EffectSpellClassMaskA_1': _masks.PWS, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


improved_inner_fire_14770 = spell(
    id=14770,
    name='Improved Inner Fire',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108, misc_value=8),
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=107, misc_value=4),
    ],
    spell_icon_id=51,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effect of your Inner Fire spell by $s1%, and increases the total number of charges by $s3.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 2, 'EffectSpellClassMaskB_1': 2, 'EffectSpellClassMaskC_1': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


improved_inner_fire_14771 = spell(
    id=14771,
    name='Improved Inner Fire',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=44, implicit_target_a=1, apply_aura=108, misc_value=8),
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=107, misc_value=4),
    ],
    spell_icon_id=51,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effect of your Inner Fire spell by $s1%, and increases the total number of charges by $s3.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 2, 'EffectSpellClassMaskB_1': 2, 'EffectSpellClassMaskC_1': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


improved_mana_burn_14772 = spell(
    id=14772,
    name='Improved Mana Burn',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1001, implicit_target_a=1, apply_aura=107, misc_value=10),
    ],
    spell_icon_id=212,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the casting time of your Mana Burn spell by $/1000;S1 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


mental_agility_14780 = spell(
    id=14780,
    name='Mental Agility',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-8, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=157,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your instant cast spells by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2470560111, 'EffectSpellClassMaskA_2': 371, 'EffectSpellClassMaskA_3': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


mental_agility_14781 = spell(
    id=14781,
    name='Mental Agility',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=157,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your instant cast spells by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2470560111, 'EffectSpellClassMaskA_2': 371, 'EffectSpellClassMaskA_3': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


silent_resolve_14784 = spell(
    id=14784,
    name='Silent Resolve',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-15, implicit_target_a=1, apply_aura=AuraType.MOD_THREAT, misc_value=66),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=107, misc_value=28),
        Effect(type=EffectType.APPLY_AURA, base_points=-15, implicit_target_a=1, apply_aura=108, misc_value=2),
    ],
    spell_icon_id=338,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the threat generated by your Holy and Discipline spells by $s1% and reduces the chance your helpful spells and damage over time effects will be dispelled by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_3': 1024, 'EffectSpellClassMaskC_1': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


silent_resolve_14785 = spell(
    id=14785,
    name='Silent Resolve',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=AuraType.MOD_THREAT, misc_value=66),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=107, misc_value=28),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=108, misc_value=2),
    ],
    spell_icon_id=338,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the threat generated by your Holy and Discipline spells by $s1% and reduces the chance your helpful spells and damage over time effects will be dispelled by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_3': 1024, 'EffectSpellClassMaskC_1': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


holy_specialization_14889 = spell(
    id=14889,
    name='Holy Specialization',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=71, misc_value=2),
    ],
    spell_icon_id=305,
    notes='Priest Holy rework (HOLY.md 0,2): 1..5% (5 ranks) -> 2/4/6% (3 ranks, rank 1: base_points 0->1). 15010/15011 orphaned.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical effect chance of your Holy spells by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 424943232, 'EffectSpellClassMaskA_2': 36, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


inspiration_14892 = spell(
    id=14892,
    name='Inspiration',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=21, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=inspiration_14893.id),
    ],
    spell_icon_id=79,
    notes="Holy rework (HOLY.md 2,3): unchanged mechanically ('none (stock 3/6/10)') - "
          "NameSubtext stripped per PLAN sec 3.1 (talent-tooltip-audit fix, WP-C).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces your target's physical damage taken by $14893s1% for $14893d after getting a critical effect from your Flash Heal, Heal, Greater Heal, Binding Heal, Penance, Prayer of Mending, Prayer of Healing, or Circle of Healing spell.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


spiritual_healing_14898 = spell(
    id=14898,
    name='Spiritual Healing',
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
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=46,
    notes="Holy rework (HOLY.md 5,2): 2/4/6/8/10% -> 3/6/10%, orphaning 15355/15356 "
          "(talent-tooltip-audit fix, WP-C).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount healed by your healing spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 419700288, 'EffectSpellClassMaskA_2': 134283268, 'EffectSpellClassMaskA_3': 4, 'EffectSpellClassMaskB_1': 419700288, 'EffectSpellClassMaskB_2': 134283268, 'EffectSpellClassMaskB_3': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


spiritual_guidance_14901 = spell(
    id=14901,
    name='Spiritual Guidance',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=174, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=175, misc_value=4),
    ],
    spell_icon_id=1873,
    notes="Holy rework (HOLY.md 4,2): 5/10/15/20/25% -> 8/16/25%, orphaning 15030/15031. WP-A's "
          "first pass left this row's base_points/NameSubtext untouched despite its own comment "
          "claiming the trim was done (talent-tooltip-audit finding, fixed in WP-C).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell power by $s1% of your total Spirit.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


improved_renew_14908 = spell(
    id=14908,
    name='Improved Renew',
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
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=321,
    notes='Priest Holy rework (HOLY.md 0,1): 5/10/15% -> 7/14/20% (rank 1: base_points 4->6).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount healed by your Renew spell by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


searing_light_14909 = spell(
    id=14909,
    name='Searing Light',
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
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=-9, implicit_target_a=1, apply_aura=108, misc_value=SpellModOp.COST),
    ],
    spell_icon_id=1868,
    notes="Priest Holy rework (HOLY.md 3,2): rank 1 - eff1/eff2 (damage +5%, unchanged from stock) "
          "mask also gains Penance's dmg-bolt bit (dw3=128) per HOLY.md's target mask ("
          "Smite|HF|Holy Nova dmg|Penance dmg bolt). New eff3 SPELLMOD_COST -8% (base_points=-9) "
          "scoped Holy Nova damage only.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Smite, Holy Fire, Holy Nova and Penance spells by $s1%, and reduces the mana cost of your Holy Nova by $s2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 5243008, 'EffectSpellClassMaskA_2': 32768, 'EffectSpellClassMaskA_3': _masks.PENANCE_BOLT, 'EffectSpellClassMaskB_1': 1048576, 'EffectSpellClassMaskC_1': _masks.HOLY_NOVA_DMG, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


mind_melt_14910 = spell(
    id=14910,
    name='Mind Melt',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, base_points=2, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=3139,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Mind Blast, Mind Flay and Mind Sear spells by $s1%, and increases the periodic critical strike chance of your Vampiric Touch, Devouring Plague and Shadow Word: Pain spells by $s2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8396800, 'EffectSpellClassMaskA_2': 524288, 'EffectSpellClassMaskB_1': 33587200, 'EffectSpellClassMaskB_2': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


healing_prayers_14911 = spell(
    id=14911,
    name='Healing Prayers',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=108, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CRITICAL_CHANCE),
    ],
    spell_icon_id=540,
    notes='Priest Holy rework (HOLY.md 4,0): eff1 mask gains Halo (dw3) so the cost reduction also '
          'covers it; new eff2 SPELLMOD_CRITICAL_CHANCE +5% (base_points=4) scoped Prayer of '
          'Healing (dw1) + Halo (dw3).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your Prayer of Healing, Prayer of Mending and Halo spells by $s1%, and increases the critical strike chance of your Prayer of Healing and Halo spells by $s2%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 512, 'EffectSpellClassMaskA_2': 32, 'EffectSpellClassMaskA_3': _masks.HALO, 'EffectSpellClassMaskB_1': _masks.POH, 'EffectSpellClassMaskB_3': _masks.HALO, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


improved_healing_14912 = spell(
    id=14912,
    name='Improved Healing',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-6, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=684,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your Greater Heal, Divine Hymn and Penance spells by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 267264, 'EffectSpellClassMaskA_2': 12582912, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


healing_focus_14913 = spell(
    id=14913,
    name='Healing Focus',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=108, misc_value=9),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL),
    ],
    spell_icon_id=1871,
    notes='Priest Holy rework (HOLY.md 0,0): pushback reduction 35% -> 50% (rank 1: base_points 34->49, '
          'keeps its existing SpellMod classmask). New eff2: generalized spell/melee/ranged haste (193, '
          'HASTE_ALL - PLAN §1) +1% (base_points=0), no classmask needed (a plain passive stat buff, '
          'not a SpellMod). Tooltip capstone line previews the (2,0/eff... ) Greater Heal/Prayer of '
          'Healing/Divine Hymn haste-stack capstone in grey on this non-final rank.\n\n'
          '|cFF9D9D9DCapstone Bonus: Completing a cast of Greater Heal, Prayer of Healing or Divine '
          'Hymn grants 2% spell haste for 10 sec, stacking up to 3 times.|r',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell, ranged and melee haste by $s2%, and reduces the pushback suffered from damaging attacks while casting any healing spell by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Completing a cast of Greater Heal, Prayer of Healing or Divine Hymn grants 2% spell haste for 10 sec, stacking up to 3 times.|r', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 269824, 'EffectSpellClassMaskA_2': 12681220, 'EffectSpellClassMaskA_3': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


holy_specialization_15008 = spell(
    id=15008,
    name='Holy Specialization',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=71, misc_value=2),
    ],
    spell_icon_id=305,
    notes='Priest Holy rework (HOLY.md 0,2): 1..5% (5 ranks) -> 2/4/6% (3 ranks, rank 2: base_points 1->3).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical effect chance of your Holy spells by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 424943232, 'EffectSpellClassMaskA_2': 36, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


holy_specialization_15009 = spell(
    id=15009,
    name='Holy Specialization',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=71, misc_value=2),
    ],
    spell_icon_id=305,
    notes='Priest Holy rework (HOLY.md 0,2): 1..5% (5 ranks) -> 2/4/6% (3 ranks, rank 3: base_points 2->5).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical effect chance of your Holy spells by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 424943232, 'EffectSpellClassMaskA_2': 36, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


holy_specialization_15010 = spell(
    id=15010,
    name='Holy Specialization',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=71, misc_value=2),
    ],
    spell_icon_id=305,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical effect chance of your Holy spells by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 424943232, 'EffectSpellClassMaskA_2': 36, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


holy_specialization_15011 = spell(
    id=15011,
    name='Holy Specialization',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=71, misc_value=2),
    ],
    spell_icon_id=305,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical effect chance of your Holy spells by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 424943232, 'EffectSpellClassMaskA_2': 36, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


healing_focus_15012 = spell(
    id=15012,
    name='Healing Focus',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=108, misc_value=9),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL),
    ],
    spell_icon_id=1871,
    notes='Priest Holy rework (HOLY.md 0,0): pushback reduction 35% -> 100% (rank 2: base_points 69->99). '
          'New eff2: generalized haste (193, HASTE_ALL) +2% (base_points=1). Final-rank capstone clause '
          'in plain color (PLAN §3.1).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell, ranged and melee haste by $s2%, and reduces the pushback suffered from damaging attacks while casting any healing spell by $s1%.\n\nCapstone Bonus: Completing a cast of Greater Heal, Prayer of Healing or Divine Hymn grants 2% spell haste for 10 sec, stacking up to 3 times.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 269824, 'EffectSpellClassMaskA_2': 12681220, 'EffectSpellClassMaskA_3': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)
procs_on(healing_focus_15012, PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS, spell_phase_mask=PROC_SPELL_PHASE_CAST,
         family_name=6, family_mask=(_masks.GREATER_HEAL | _masks.POH, _masks.DIVINE_HYMN, 0), chance=100)
scripted_by(healing_focus_15012, 'spell_pri_healing_focus_capstone')


improved_healing_15013 = spell(
    id=15013,
    name='Improved Healing',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=684,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your Greater Heal, Divine Hymn and Penance spells by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 267264, 'EffectSpellClassMaskA_2': 12582912, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


improved_healing_15014 = spell(
    id=15014,
    name='Improved Healing',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-16, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=684,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your Greater Heal, Divine Hymn and Penance spells by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 267264, 'EffectSpellClassMaskA_2': 12582912, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


searing_light_15017 = spell(
    id=15017,
    name='Searing Light',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-17, implicit_target_a=1, apply_aura=108, misc_value=SpellModOp.COST),
    ],
    spell_icon_id=1868,
    notes="Priest Holy rework (HOLY.md 3,2): rank 2 - mask gains Penance dmg-bolt bit (dw3=128). New "
          "eff3 SPELLMOD_COST -16% (base_points=-17) scoped Holy Nova damage.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Smite, Holy Fire, Holy Nova and Penance spells by $s1%, and reduces the mana cost of your Holy Nova by $s2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 5243008, 'EffectSpellClassMaskA_2': 32768, 'EffectSpellClassMaskA_3': _masks.PENANCE_BOLT, 'EffectSpellClassMaskB_1': 1048576, 'EffectSpellClassMaskC_1': _masks.HOLY_NOVA_DMG, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


healing_prayers_15018 = spell(
    id=15018,
    name='Healing Prayers',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=108, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CRITICAL_CHANCE),
    ],
    spell_icon_id=540,
    notes='Priest Holy rework (HOLY.md 4,0): rank 2, cost -20% (mask += Halo dw3), new eff2 crit +10% '
          '(base_points=9) scoped PoH (dw1) + Halo (dw3).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your Prayer of Healing, Prayer of Mending and Halo spells by $s1%, and increases the critical strike chance of your Prayer of Healing and Halo spells by $s2%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 512, 'EffectSpellClassMaskA_2': 32, 'EffectSpellClassMaskA_3': _masks.HALO, 'EffectSpellClassMaskB_1': _masks.POH, 'EffectSpellClassMaskB_3': _masks.HALO, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


improved_renew_15020 = spell(
    id=15020,
    name='Improved Renew',
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
        Effect(type=EffectType.APPLY_AURA, base_points=13, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=321,
    notes='Priest Holy rework (HOLY.md 0,1): 5/10/15% -> 7/14/20% (rank 2: base_points 9->13).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount healed by your Renew spell by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


spiritual_guidance_15028 = spell(
    id=15028,
    name='Spiritual Guidance',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=174, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=175, misc_value=4),
    ],
    spell_icon_id=1873,
    notes="Holy rework (HOLY.md 4,2): 5/10/15/20/25% -> 8/16/25% (talent-tooltip-audit fix, WP-C).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell power by $s1% of your total Spirit.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


spiritual_guidance_15029 = spell(
    id=15029,
    name='Spiritual Guidance',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=174, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=175, misc_value=4),
    ],
    spell_icon_id=1873,
    notes="Holy rework (HOLY.md 4,2): 5/10/15/20/25% -> 8/16/25% (talent-tooltip-audit fix, WP-C).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell power by $s1% of your total Spirit.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


spiritual_guidance_15030 = spell(
    id=15030,
    name='Spiritual Guidance',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=174, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=175, misc_value=4),
    ],
    spell_icon_id=1873,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell power by $s1% of your total Spirit.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


spiritual_guidance_15031 = spell(
    id=15031,
    name='Spiritual Guidance',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=174, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=175, misc_value=4),
    ],
    spell_icon_id=1873,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell power by $s1% of your total Spirit.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


shadow_weaving_15257 = spell(
    id=15257,
    name='Shadow Weaving',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=6, apply_aura=109, trigger_spell=15258),
    ],
    spell_icon_id=9,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Shadow damage spells have a $s1% chance to increase the Shadow damage you deal by $15258s1% for $15258d.  Stacks up to $15258u times.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 42508304, 'EffectSpellClassMaskA_2': 525314, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


darkness_15259 = spell(
    id=15259,
    name='Darkness',
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
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=164,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Shadow spell damage by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 41951232, 'EffectSpellClassMaskA_2': 524290, 'EffectSpellClassMaskB_1': 33587200, 'EffectSpellClassMaskB_2': 1024, 'EffectSpellClassMaskC_1': 524288, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


shadow_focus_15260 = spell(
    id=15260,
    name='Shadow Focus',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=107, misc_value=16),
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=208,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your chance to hit with your Shadow spells by $s1%, and reduces the mana cost of your Shadow spells by $s2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 109814020, 'EffectSpellClassMaskA_2': 3933258, 'EffectSpellClassMaskA_3': 8520, 'EffectSpellClassMaskB_1': 42197252, 'EffectSpellClassMaskB_2': 2150894914, 'EffectSpellClassMaskB_3': 8256, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


shadow_affinity_15272 = spell(
    id=15272,
    name='Shadow Affinity',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-17, implicit_target_a=1, apply_aura=108, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=23),
    ],
    spell_icon_id=178,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the threat generated by your Shadow spells by $s1%, and you receive $s2% of your base mana when your Shadow Word: Pain or Vampiric Touch spells are dispelled.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 109814020, 'EffectSpellClassMaskA_2': 787530, 'EffectSpellClassMaskA_3': 8256, 'EffectSpellClassMaskB_1': 32768, 'EffectSpellClassMaskB_2': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


improved_mind_blast_15273 = spell(
    id=15273,
    name='Improved Mind Blast',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-501, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.DUMMY, base_points=19, implicit_target_a=1),
    ],
    spell_icon_id=95,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Mind Blast spell by $/1000;S1 sec., and while in Shadowform your Mind Blast also has a $s2% chance to reduce all healing done to the target by $48301s1% for $48301d.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


veiled_shadows_15274 = spell(
    id=15274,
    name='Veiled Shadows',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-3001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=-60001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=331,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Decreases the cooldown of your Fade ability by $/1000;s1 sec, and reduces the cooldown of your Shadowfiend ability by 1 minute.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 16384, 'EffectSpellClassMaskB_2': 256, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


improved_shadow_word_pain_15275 = spell(
    id=15275,
    name='Improved Shadow Word: Pain',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=234,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Shadow Word: Pain spell by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 32768, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


vampiric_embrace_15286 = spell(
    id=15286,
    name='Vampiric Embrace',
    school=School.SHADOW,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=150,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$15286s1% of single-target Shadow spell damage caused by casting priest heals the priest and $/5;15286s1% heals the group.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Fills you with the embrace of Shadow energy, causing you to be healed for $15286s1% and other party members to be healed for $/5;15286s1% of any single-target Shadow spell damage you deal for $15286d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 327680, 'RangeIndex': 1, 'SpellClassMask_1': 4, 'SpellClassSet': 6, 'SpellLevel': 1, 'SpellVisualID_1': 3582, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


darkness_15307 = spell(
    id=15307,
    name='Darkness',
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
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=164,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Shadow spell damage by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 41951232, 'EffectSpellClassMaskA_2': 524290, 'EffectSpellClassMaskB_1': 33587200, 'EffectSpellClassMaskB_2': 1024, 'EffectSpellClassMaskC_1': 524288, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


darkness_15308 = spell(
    id=15308,
    name='Darkness',
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
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=164,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Shadow spell damage by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 41951232, 'EffectSpellClassMaskA_2': 524290, 'EffectSpellClassMaskB_1': 33587200, 'EffectSpellClassMaskB_2': 1024, 'EffectSpellClassMaskC_1': 524288, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


darkness_15309 = spell(
    id=15309,
    name='Darkness',
    school=School.NORMAL,
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
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=164,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Shadow spell damage by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 41951232, 'EffectSpellClassMaskA_2': 524290, 'EffectSpellClassMaskB_1': 33587200, 'EffectSpellClassMaskB_2': 1024, 'EffectSpellClassMaskC_1': 524288, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


darkness_15310 = spell(
    id=15310,
    name='Darkness',
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
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=164,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Shadow spell damage by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 41951232, 'EffectSpellClassMaskA_2': 524290, 'EffectSpellClassMaskB_1': 33587200, 'EffectSpellClassMaskB_2': 1024, 'EffectSpellClassMaskC_1': 524288, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


veiled_shadows_15311 = spell(
    id=15311,
    name='Veiled Shadows',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-6001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=-120001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=331,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Decreases the cooldown of your Fade ability by $/1000;s1 sec, and reduces the cooldown of your Shadowfiend ability by 2 minutes.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 16384, 'EffectSpellClassMaskB_2': 256, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


improved_mind_blast_15312 = spell(
    id=15312,
    name='Improved Mind Blast',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.DUMMY, base_points=39, implicit_target_a=1),
    ],
    spell_icon_id=95,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Mind Blast spell by $/1000;S1 sec., and while in Shadowform your Mind Blast also has a $s2% chance to reduce all healing done to the target by $48301s1% for $48301d.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


improved_mind_blast_15313 = spell(
    id=15313,
    name='Improved Mind Blast',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1501, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.DUMMY, base_points=59, implicit_target_a=1),
    ],
    spell_icon_id=95,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Mind Blast spell by $/1000;S1 sec., and while in Shadowform your Mind Blast also has a $s2% chance to reduce all healing done to the target by $48301s1% for $48301d.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


improved_mind_blast_15314 = spell(
    id=15314,
    name='Improved Mind Blast',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-2001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.DUMMY, base_points=79, implicit_target_a=1),
    ],
    spell_icon_id=95,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Mind Blast spell by $/1000;S1 sec., and while in Shadowform your Mind Blast also has a $s2% chance to reduce all healing done to the target by $48301s1% for $48301d.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


improved_mind_blast_15316 = spell(
    id=15316,
    name='Improved Mind Blast',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-2501, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.DUMMY, base_points=99, implicit_target_a=1),
    ],
    spell_icon_id=95,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Mind Blast spell by $/1000;S1 sec., and while in Shadowform your Mind Blast also has a $s2% chance to reduce all healing done to the target by $48301s1% for $48301d.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


improved_shadow_word_pain_15317 = spell(
    id=15317,
    name='Improved Shadow Word: Pain',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=234,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Shadow Word: Pain spell by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 32768, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


shadow_affinity_15318 = spell(
    id=15318,
    name='Shadow Affinity',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-9, implicit_target_a=1, apply_aura=108, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=23),
    ],
    spell_icon_id=178,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the threat generated by your Shadow spells by $s1%, and you receive $s2% of your base mana when your Shadow Word: Pain or Vampiric Touch spells are dispelled.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 109814020, 'EffectSpellClassMaskA_2': 787530, 'EffectSpellClassMaskA_3': 8256, 'EffectSpellClassMaskB_1': 32768, 'EffectSpellClassMaskB_2': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


shadow_affinity_15320 = spell(
    id=15320,
    name='Shadow Affinity',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-26, implicit_target_a=1, apply_aura=108, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=23),
    ],
    spell_icon_id=178,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the threat generated by your Shadow spells by $s1%, and you receive $s2% of your base mana when your Shadow Word: Pain or Vampiric Touch spells are dispelled.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 109814020, 'EffectSpellClassMaskA_2': 787530, 'EffectSpellClassMaskA_3': 8256, 'EffectSpellClassMaskB_1': 32768, 'EffectSpellClassMaskB_2': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


shadow_focus_15327 = spell(
    id=15327,
    name='Shadow Focus',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=16),
        Effect(type=EffectType.APPLY_AURA, base_points=-5, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=208,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your chance to hit with your Shadow spells by $s1%, and reduces the mana cost of your Shadow spells by $s2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 109814020, 'EffectSpellClassMaskA_2': 3933258, 'EffectSpellClassMaskA_3': 8520, 'EffectSpellClassMaskB_1': 42197252, 'EffectSpellClassMaskB_2': 2150894914, 'EffectSpellClassMaskB_3': 8256, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


shadow_focus_15328 = spell(
    id=15328,
    name='Shadow Focus',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=107, misc_value=16),
        Effect(type=EffectType.APPLY_AURA, base_points=-7, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=208,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your chance to hit with your Shadow spells by $s1%, and reduces the mana cost of your Shadow spells by $s2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 109814020, 'EffectSpellClassMaskA_2': 3933258, 'EffectSpellClassMaskA_3': 8520, 'EffectSpellClassMaskB_1': 42197252, 'EffectSpellClassMaskB_2': 2150894914, 'EffectSpellClassMaskB_3': 8256, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


shadow_weaving_15331 = spell(
    id=15331,
    name='Shadow Weaving',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=65, implicit_target_a=6, apply_aura=109, trigger_spell=15258),
    ],
    spell_icon_id=9,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Shadow damage spells have a $s1% chance to increase the Shadow damage you deal by $15258s1% for $15258d.  Stacks up to $15258u times.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 42508304, 'EffectSpellClassMaskA_2': 525314, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


shadow_weaving_15332 = spell(
    id=15332,
    name='Shadow Weaving',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=6, apply_aura=109, trigger_spell=15258),
    ],
    spell_icon_id=9,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Shadow damage spells have a $s1% chance to increase the Shadow damage you deal by $15258s1% for $15258d.  Stacks up to $15258u times.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 42508304, 'EffectSpellClassMaskA_2': 525314, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


improved_spirit_tap_15337 = spell(
    id=15337,
    name='Improved Spirit Tap',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=improved_spirit_tap_49694.id),
    ],
    spell_icon_id=152,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Mind Blast and Shadow Word: Death critical strikes have a 100% chance and your Mind Flay critical strikes have a 50% chance to increase your total Spirit by $49694s1%. For the duration, your mana will regenerate at a $49694s2% rate while casting. Lasts $49694d.', 'EffectBasePoints_2': 99, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 6},
)


improved_spirit_tap_15338 = spell(
    id=15338,
    name='Improved Spirit Tap',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=59000),
    ],
    spell_icon_id=152,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Mind Blast and Shadow Word: Death critical strikes have a 100% chance and your Mind Flay critical strikes have a 50% chance to increase your total Spirit by $59000s1%. For the duration, your mana will regenerate at a $59000s2% rate while casting. Lasts $49694d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 6},
)


spiritual_healing_15349 = spell(
    id=15349,
    name='Spiritual Healing',
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
    spell_icon_id=46,
    notes="Holy rework (HOLY.md 5,2): 2/4/6/8/10% -> 3/6/10% (talent-tooltip-audit fix, WP-C).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount healed by your healing spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 419700288, 'EffectSpellClassMaskA_2': 134283268, 'EffectSpellClassMaskA_3': 4, 'EffectSpellClassMaskB_1': 419700288, 'EffectSpellClassMaskB_2': 134283268, 'EffectSpellClassMaskB_3': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


spiritual_healing_15354 = spell(
    id=15354,
    name='Spiritual Healing',
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
    spell_icon_id=46,
    notes="Holy rework (HOLY.md 5,2): 2/4/6/8/10% -> 3/6/10% (talent-tooltip-audit fix, WP-C).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount healed by your healing spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 419700288, 'EffectSpellClassMaskA_2': 134283268, 'EffectSpellClassMaskA_3': 4, 'EffectSpellClassMaskB_1': 419700288, 'EffectSpellClassMaskB_2': 134283268, 'EffectSpellClassMaskB_3': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


spiritual_healing_15355 = spell(
    id=15355,
    name='Spiritual Healing',
    school=School.NORMAL,
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
    spell_icon_id=46,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount healed by your healing spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 419700288, 'EffectSpellClassMaskA_2': 134283268, 'EffectSpellClassMaskA_3': 4, 'EffectSpellClassMaskB_1': 419700288, 'EffectSpellClassMaskB_2': 134283268, 'EffectSpellClassMaskB_3': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


spiritual_healing_15356 = spell(
    id=15356,
    name='Spiritual Healing',
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
    spell_icon_id=46,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount healed by your healing spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 419700288, 'EffectSpellClassMaskA_2': 134283268, 'EffectSpellClassMaskA_3': 4, 'EffectSpellClassMaskB_1': 419700288, 'EffectSpellClassMaskB_2': 134283268, 'EffectSpellClassMaskB_3': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


inspiration_15362 = spell(
    id=15362,
    name='Inspiration',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=21, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=15357),
    ],
    spell_icon_id=79,
    notes="Holy rework (HOLY.md 2,3): unchanged mechanically - NameSubtext stripped per PLAN "
          "sec 3.1 (talent-tooltip-audit fix, WP-C).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces your target's physical damage taken by $15357s1% for $15357d after getting a critical effect from your Flash Heal, Heal, Greater Heal, Binding Heal, Penance, Prayer of Mending, Prayer of Healing, or Circle of Healing spell.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


inspiration_15363 = spell(
    id=15363,
    name='Inspiration',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=21, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=15359),
    ],
    spell_icon_id=79,
    notes="Holy rework (HOLY.md 2,3): unchanged mechanically - NameSubtext stripped per PLAN "
          "sec 3.1 (talent-tooltip-audit fix, WP-C).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces your target's physical damage taken by $15359s1% for $15359d after getting a critical effect from your Flash Heal, Heal, Greater Heal, Binding Heal, Penance, Prayer of Mending, Prayer of Healing, or Circle of Healing spell.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


improved_psychic_scream_15392 = spell(
    id=15392,
    name='Improved Psychic Scream',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-2001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=1488,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Psychic Scream spell by $/1000;s1 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 65536, 'EffectSpellClassMaskA_1': 65536, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


improved_psychic_scream_15448 = spell(
    id=15448,
    name='Improved Psychic Scream',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-4001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=1488,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Psychic Scream spell by $/1000;s1 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 65536, 'EffectSpellClassMaskA_1': 65536, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


improved_renew_17191 = spell(
    id=17191,
    name='Improved Renew',
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
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=321,
    notes='Priest Holy rework (HOLY.md 0,1): 5/10/15% -> 7/14/20% (rank 3: base_points 14->19).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount healed by your Renew spell by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


shadow_reach_17322 = spell(
    id=17322,
    name='Shadow Reach',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=5),
    ],
    spell_icon_id=55,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of your offensive Shadow spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 109223940, 'EffectSpellClassMaskA_2': 3147010, 'EffectSpellClassMaskA_3': 8256, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


shadow_reach_17323 = spell(
    id=17323,
    name='Shadow Reach',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=5),
    ],
    spell_icon_id=55,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of your offensive Shadow spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 109223940, 'EffectSpellClassMaskA_2': 3147010, 'EffectSpellClassMaskA_3': 8256, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


divine_fury_18530 = spell(
    id=18530,
    name='Divine Fury',
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
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CRITICAL_CHANCE),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=307,
    notes='Priest Holy rework (HOLY.md 1,2): rebuilt from a cast-time SpellMod into eff1'
          'ADD_FLAT_MODIFIER SPELLMOD_CRITICAL_CHANCE +2% scoped to Holy Fire (dw1) - rank 1 '
          '(base_points=1) - and eff2 DUMMY +3% (base_points=2, marker read by '
          'Priest::ApplyDoneDamagePctMods for "direct Holy damage vs your Holy Fire DoT target").',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Holy Fire spell by $s1%, and increases direct Holy damage done to targets afflicted by your Holy Fire by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': _masks.HOLY_FIRE, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


divine_fury_18531 = spell(
    id=18531,
    name='Divine Fury',
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
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CRITICAL_CHANCE),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=307,
    notes='Priest Holy rework (HOLY.md 1,2): rank 2 - crit +4% (base_points=3), damage +6% (base_points=5).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Holy Fire spell by $s1%, and increases direct Holy damage done to targets afflicted by your Holy Fire by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': _masks.HOLY_FIRE, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


divine_fury_18533 = spell(
    id=18533,
    name='Divine Fury',
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
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CRITICAL_CHANCE),
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=307,
    notes='Priest Holy rework (HOLY.md 1,2): rank 3 - crit +6% (base_points=5), damage +9% (base_points=8).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Holy Fire spell by $s1%, and increases direct Holy damage done to targets afflicted by your Holy Fire by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': _masks.HOLY_FIRE, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


divine_fury_18534 = spell(
    id=18534,
    name='Divine Fury',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-401, implicit_target_a=1, apply_aura=107, misc_value=10),
    ],
    spell_icon_id=307,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the casting time of your Smite, Holy Fire, Heal and Greater Heal spells by $/1000;S1 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 1053824, 'EffectSpellClassMaskA_1': 1053824, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


divine_fury_18535 = spell(
    id=18535,
    name='Divine Fury',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-501, implicit_target_a=1, apply_aura=107, misc_value=10),
    ],
    spell_icon_id=307,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the casting time of your Smite, Holy Fire, Heal and Greater Heal spells by $/1000;S1 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 1053824, 'EffectSpellClassMaskA_1': 1053824, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


spirit_of_redemption_20711 = spell(
    id=20711,
    name='Spirit of Redemption',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=137, misc_value=4),
    ],
    spell_icon_id=1654,
    notes='Priest Holy rework (HOLY.md 4,1): now 3 ranks - this row is rank 1 (Spirit +3%, '
          'base_points=2). The stock DUMMY effect is REMOVED (not just left inert): '
          "Unit::Kill's on-death hardcode (Unit.cpp:13787-13830, deleted by this pass per PLAN "
          '§6.8) keys on GetAuraEffectDummy(20711), so dropping the DUMMY here retires the old '
          'on-death form with zero core changes - the new capstone form (200191-200194/200226) '
          'is entirely script-driven instead (spell_pri_spirit_of_redemption on 200192). Capstone '
          'preview text added per PLAN sec 3.1 (talent-tooltip-audit fix, WP-C: was missing on '
          'this non-final rank entirely).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'BaseLevel': 30, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases total Spirit by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Absorb otherwise lethal damage up to 300% of Spirit. If it prevents death, become a Spirit of Redemption for 5 sec: cannot move or attack, 50% reduced damage taken, Holy Priest heals cost no mana. Shares a 2 min cooldown with Ardent Defender and Cheat Death.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_3': 512, 'SpellClassSet': 6, 'SpellLevel': 30},
)


holy_reach_27789 = spell(
    id=27789,
    name='Holy Reach',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.RANGE),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=SpellModOp.RADIUS),
    ],
    spell_icon_id=300,
    notes="Priest Holy rework (HOLY.md 3,0/design doc row 3,0): rank 1 - eff1 changed from the "
          "stock ADD_PCT_MODIFIER (+10% range) to ADD_FLAT_MODIFIER +3 yd (base_points=2) per the "
          "design doc's own '+3/6 yd' wording (a flat distance, not a percentage) - this is a real "
          "aura-type change, not just a value tweak. Mask replaced with Shadow Reach's own live "
          "mask (17322: dw1=109223940, "
          "dw2=3147010, dw3=8256 - Mind Blast/Mind Sear/Vampiric Touch/Mind Flay) PLUS Smite|Holy "
          "Fire on dw1, per HOLY.md's literal instruction. eff2 (SPELLMOD_RADIUS) mask gains Holy "
          "Word: Sanctify (dw3) alongside the existing Divine Hymn pulse tag (dw3=4, confirmed via "
          "divine_hymn_64844's own SpellClassMask_3=4 elsewhere in this file) - dw1 (406848000 = "
          "Prayer of Healing|Circle of Healing|Holy Nova heal, unchanged) is left untouched.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of your damaging spells with a cast or channel by $s1 yds, and the radius of your Prayer of Healing, Holy Nova, Divine Hymn, Circle of Healing and Holy Word: Sanctify spells by $s2%.\n\n|cFF9D9D9DCapstone Bonus: Directly healing or damaging a target beyond 20 yds has a 20% chance to restore 2% of missing mana over 4 sec, once per 15 sec.|r', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 110272644, 'EffectSpellClassMaskA_2': 3147010, 'EffectSpellClassMaskA_3': 8256, 'EffectSpellClassMaskB_1': 406848000, 'EffectSpellClassMaskB_3': 16777220, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


holy_reach_27790 = spell(
    id=27790,
    name='Holy Reach',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.RANGE),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=SpellModOp.RADIUS),
    ],
    spell_icon_id=300,
    notes="Priest Holy rework (HOLY.md 3,0): rank 2 - eff1 +6 yd (base_points=5, ADD_FLAT_MODIFIER, "
          "same aura-type change as rank 1). eff2 radius +20% unchanged, mask gains Holy Word: "
          "Sanctify (dw3) same as rank 1. This rank's own top-level 'SpellClassMask_2': 4194304 "
          "(Divine Hymn CHANNEL's own dw2 tag, 64843) is left as-is - a spell-wide field, not tied "
          "to either per-effect classmask - since HOLY.md never asked for it to change.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of your damaging spells with a cast or channel by $s1 yds, and the radius of your Prayer of Healing, Holy Nova, Divine Hymn, Circle of Healing and Holy Word: Sanctify spells by $s2%.\n\nCapstone Bonus: Directly healing or damaging a target beyond 20 yds has a 20% chance to restore 2% of missing mana over 4 sec, once per 15 sec.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 110272644, 'EffectSpellClassMaskA_2': 3147010, 'EffectSpellClassMaskA_3': 8256, 'EffectSpellClassMaskB_1': 406848000, 'EffectSpellClassMaskB_3': 16777220, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 4194304, 'SpellClassSet': 6},
)
procs_on(holy_reach_27790, PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS | PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG,
         spell_phase_mask=PROC_SPELL_PHASE_HIT, chance=20, cooldown_ms=15000)
scripted_by(holy_reach_27790, 'spell_pri_holy_reach_capstone')


blessed_recovery_27811 = spell(
    id=27811,
    name='Blessed Recovery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=1875,
    notes='Priest Holy rework (HOLY.md 1,1): rebuilt from the old "heal % of a melee/ranged crit taken" '
          'proc into a flat "Priest healing effectiveness +3/6/9%" SpellMod (ADD_PCT_MODIFIER '
          'SPELLMOD_DAMAGE, scoped PRIEST_HEAL_MASK on all three dwords) - rank 1 (base_points=2). '
          'ProcTypeMask/ProcChance dropped: this rank no longer procs on anything itself (the capstone '
          'proc lives on rank 3, 27816, below). 27813 (the old instant-heal-over-time payout aura) is '
          'now unused - 200177/200178 replace it. Capstone preview text added per PLAN sec 3.1 '
          '(talent-tooltip-audit fix, WP-C: was missing on this non-final rank entirely).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effectiveness of your healing spells by $s1%.\n\n|cFF9D9D9DCapstone Bonus: When your Renew heals a target at or below 35% health, immediately heal them for an additional 2 ticks worth without consuming duration. Occurs once per 20 sec per target.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': _masks.PRIEST_HEAL_MASK[0], 'EffectSpellClassMaskA_2': _masks.PRIEST_HEAL_MASK[1], 'EffectSpellClassMaskA_3': _masks.PRIEST_HEAL_MASK[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


blessed_recovery_27815 = spell(
    id=27815,
    name='Blessed Recovery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=1875,
    notes='Priest Holy rework (HOLY.md 1,1): rank 2, +6% (base_points=5). Capstone preview text '
          'added per PLAN sec 3.1 (talent-tooltip-audit fix, WP-C).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effectiveness of your healing spells by $s1%.\n\n|cFF9D9D9DCapstone Bonus: When your Renew heals a target at or below 35% health, immediately heal them for an additional 2 ticks worth without consuming duration. Occurs once per 20 sec per target.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': _masks.PRIEST_HEAL_MASK[0], 'EffectSpellClassMaskA_2': _masks.PRIEST_HEAL_MASK[1], 'EffectSpellClassMaskA_3': _masks.PRIEST_HEAL_MASK[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


blessed_recovery_27816 = spell(
    id=27816,
    name='Blessed Recovery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=1875,
    notes='Priest Holy rework (HOLY.md 1,1): rank 3, +9% (base_points=8) plus the capstone: your Renew '
          'healing a target at or below 35% health immediately heals them for 2 more ticks worth, once '
          'per 20 sec per target (spell_pri_blessed_recovery, rewritten). procs_on gates the AuraScript '
          'to Renew/Empowered Renew-chunk periodic or direct-heal events only, per HOLY.md/design doc §5.5. '
          'Non-final ranks show the identical clause in grey as a preview (PLAN §3.1).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effectiveness of your healing spells by $s1%.\n\nCapstone Bonus: When your Renew heals a target at or below 35% health, immediately heal them for an additional 2 ticks worth without consuming duration. Occurs once per 20 sec per target.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': _masks.PRIEST_HEAL_MASK[0], 'EffectSpellClassMaskA_2': _masks.PRIEST_HEAL_MASK[1], 'EffectSpellClassMaskA_3': _masks.PRIEST_HEAL_MASK[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)
procs_on(blessed_recovery_27816, PROC_FLAG_DONE_PERIODIC | PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS,
         family_name=6, family_mask=(_masks.RENEW, 0, 0), spell_type_mask=PROC_SPELL_TYPE_HEAL, chance=100)
scripted_by(blessed_recovery_27816, 'spell_pri_blessed_recovery')


improved_vampiric_embrace_27839 = spell(
    id=27839,
    name='Improved Vampiric Embrace',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=1, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=1876,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the healing received from Vampiric Embrace by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


improved_vampiric_embrace_27840 = spell(
    id=27840,
    name='Improved Vampiric Embrace',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=66, implicit_target_a=1, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=1876,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the healing received from Vampiric Embrace by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


spell_warding_27900 = spell(
    id=27900,
    name='Spell Warding',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
    ],
    spell_icon_id=1880,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces all spell damage taken by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


spell_warding_27901 = spell(
    id=27901,
    name='Spell Warding',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
    ],
    spell_icon_id=1880,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces all spell damage taken by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


spell_warding_27902 = spell(
    id=27902,
    name='Spell Warding',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-7, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
    ],
    spell_icon_id=1880,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces all spell damage taken by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


spell_warding_27903 = spell(
    id=27903,
    name='Spell Warding',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-9, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
    ],
    spell_icon_id=1880,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces all spell damage taken by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


spell_warding_27904 = spell(
    id=27904,
    name='Spell Warding',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
    ],
    spell_icon_id=1880,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces all spell damage taken by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


blessed_resilience_33142 = spell(
    id=33142,
    name='Blessed Resilience',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=33143),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=136, misc_value=127),
    ],
    spell_icon_id=2177,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effectiveness of your healing spells by $s2%, and critical hits made against you have a $h% chance to prevent you from being critically hit again for $33143d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'ProcTypeMask': 664232, 'RangeIndex': 1, 'SpellClassSet': 6},
)


blessed_resilience_33145 = spell(
    id=33145,
    name='Blessed Resilience',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=33143),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=136, misc_value=127),
    ],
    spell_icon_id=2177,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effectiveness of your healing spells by $s2%, and critical hits made against you have a $h% chance to prevent you from being critically hit again for $33143d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 40, 'ProcTypeMask': 664232, 'RangeIndex': 1, 'SpellClassSet': 6},
)


blessed_resilience_33146 = spell(
    id=33146,
    name='Blessed Resilience',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=33143),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=136, misc_value=127),
    ],
    spell_icon_id=2177,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effectiveness of your healing spells by $s2%, and critical hits made against you have a $h% chance to prevent you from being critically hit again for $33143d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 60, 'ProcTypeMask': 664232, 'RangeIndex': 1, 'SpellClassSet': 6},
)


surge_of_light_33150 = spell(
    id=33150,
    name='Surge of Light',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=33151),
    ],
    spell_icon_id=2176,
    notes='Priest Holy rework (HOLY.md 5,0): rank 1, 10% (procs_on chance below replaces the stock '
          'ProcChance/ProcTypeMask row - direct-crit only, no periodic flags).',
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your direct damage and healing criticals have a 10% chance to cause your next Smite or Flash Heal spell to be instant cast and cost no mana. Stacks up to 2 times.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)
procs_on(surge_of_light_33150, PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG | PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS,
         hit_mask=PROC_HIT_CRITICAL, chance=10)


surge_of_light_33154 = spell(
    id=33154,
    name='Surge of Light',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=33151),
    ],
    spell_icon_id=2176,
    notes='Priest Holy rework (HOLY.md 5,0): rank 2, 20%.',
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your direct damage and healing criticals have a 20% chance to cause your next Smite or Flash Heal spell to be instant cast and cost no mana. Stacks up to 2 times.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)
procs_on(surge_of_light_33154, PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG | PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS,
         hit_mask=PROC_HIT_CRITICAL, chance=20)
# spell_pri_surge_of_light_consume binds on Smite (585) and Flash Heal (2061) themselves (HOLY.md
# 5,0's Script column), not on these talent ranks - see the scripted_by() calls next to those two
# spells in priest_spells.py.


empowered_healing_33158 = spell(
    id=33158,
    name='Empowered Healing',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=107, misc_value=24),
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=107, misc_value=24),
    ],
    spell_icon_id=241,
    notes="Priest Holy rework (HOLY.md 7,1): 7/15/23% (5 ranks) -> 8/16/25% (3 ranks - stored 7/15/24 "
          "per die_sides=1 convention). Rank 1's target (8%) matches the stock value already "
          '(base_points=7 unchanged); eff2 mask gains Halo (dw3).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Greater Heal, Flash Heal, Binding Heal and Halo gain an additional $s1% of your bonus healing effects.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskB_1': 2048, 'EffectSpellClassMaskB_2': 4, 'EffectSpellClassMaskB_3': _masks.HALO, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


empowered_healing_33159 = spell(
    id=33159,
    name='Empowered Healing',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=107, misc_value=24),
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=107, misc_value=24),
    ],
    spell_icon_id=241,
    notes='Priest Holy rework (HOLY.md 7,1): rank 2, target 16% matches the stock value already '
          '(base_points=15 unchanged); eff2 mask gains Halo (dw3).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Greater Heal, Flash Heal, Binding Heal and Halo gain an additional $s1% of your bonus healing effects.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskB_1': 2048, 'EffectSpellClassMaskB_2': 4, 'EffectSpellClassMaskB_3': _masks.HALO, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


empowered_healing_33160 = spell(
    id=33160,
    name='Empowered Healing',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=107, misc_value=24),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=107, misc_value=24),
    ],
    spell_icon_id=241,
    notes='Priest Holy rework (HOLY.md 7,1): rank 3 (now the final kept rank), 23% -> 25% '
          '(base_points 23->24); eff2 bumped to match (was 11/12%, now the same 24 as eff1) and its '
          'mask gains Halo (dw3).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Greater Heal, Flash Heal, Binding Heal and Halo gain an additional $s1% of your bonus healing effects.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskB_1': 2048, 'EffectSpellClassMaskB_2': 4, 'EffectSpellClassMaskB_3': _masks.HALO, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


empowered_healing_33161 = spell(
    id=33161,
    name='Empowered Healing',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=31, implicit_target_a=1, apply_aura=107, misc_value=24),
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=107, misc_value=24),
    ],
    spell_icon_id=241,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Greater Heal spell gains an additional $s1% and your Flash Heal and Binding Heal gain an additional $s2% of your bonus healing effects.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskB_1': 2048, 'EffectSpellClassMaskB_2': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


empowered_healing_33162 = spell(
    id=33162,
    name='Empowered Healing',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=107, misc_value=24),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=107, misc_value=24),
    ],
    spell_icon_id=241,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Greater Heal spell gains an additional $s1% and your Flash Heal and Binding Heal gain an additional $s2% of your bonus healing effects.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskB_1': 2048, 'EffectSpellClassMaskB_2': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


# Priest Discipline rework (docs/reworks/priest-disc-rework.md (3,0)): Absolution's old "reduces the
# mana cost of your dispel spells" SpellMod is cut entirely (its dispel-cost niche was rolled into
# the baseline Dispel Magic change) and replaced by a single SPELL_AURA_DUMMY carrying the tuned
# crit percentage. spell_pri_absolution (registered on Dispel Magic 527, and on Mass Dispel's two
# effects 32375/32592 - the friendly and hostile purge halves) reads it through the marker-aura-by-
# icon idiom - GetDummyAuraEffect(SPELLFAMILY_PRIEST, 2212, EFFECT_0),
# icon 2212 (Spell_Holy_Absolution) being unique to these three rows inside the priest family - and
# casts absolution_buff_200153 with the amount as BP0, on its own 30 s cooldown.
_ABSOLUTION_NOTE = (
    'Discipline rework (3,0): dispel-cost SpellMod replaced by a DUMMY marker (8/16/25) read by '
    'spell_pri_absolution, which grants absolution_buff_200153 on a successful magic dispel.'
)


absolution_33167 = spell(
    id=33167,
    name='Absolution',
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
        ApplyAura(AuraType.DUMMY, base_points=7, implicit_target_a=1),
    ],
    spell_icon_id=2212,
    notes=_ABSOLUTION_NOTE,
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Dispelling or purging a magic effect grants Absolution, increasing your spell critical strike chance by 8% for 10 sec.  Cannot occur more than once every 30 sec.', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


absolution_33171 = spell(
    id=33171,
    name='Absolution',
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
        ApplyAura(AuraType.DUMMY, base_points=15, implicit_target_a=1),
    ],
    spell_icon_id=2212,
    notes=_ABSOLUTION_NOTE,
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Dispelling or purging a magic effect grants Absolution, increasing your spell critical strike chance by 16% for 10 sec.  Cannot occur more than once every 30 sec.', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


absolution_33172 = spell(
    id=33172,
    name='Absolution',
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
        ApplyAura(AuraType.DUMMY, base_points=24, implicit_target_a=1),
    ],
    spell_icon_id=2212,
    notes=_ABSOLUTION_NOTE,
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Dispelling or purging a magic effect grants Absolution, increasing your spell critical strike chance by 25% for 10 sec.  Cannot occur more than once every 30 sec.', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


# Priest Discipline rework (docs/reworks/priest-disc-rework.md (5,0)): the stock Mass Dispel
# cast-time SpellMod (eff1, SPELLMOD_CASTING_TIME scoped to the Mass Dispel bit) is cut - the spec
# drops that clause - so eff1 is empty on rank 1 and becomes the capstone DUMMY marker on rank 2.
# eff2/eff3 (SPELL_AURA_MOD_DAMAGE_PERCENT_DONE misc 126, SPELL_AURA_MOD_HEALING_DONE_PERCENT misc
# 127) deliberately keep their exact stock slots and amounts (+2/4%); their leftover stock
# EffectSpellClassMaskB_*/C_* bytes are kept untouched too - AC reads neither aura through a
# classmask (both are school-mask-only paths in Unit::SpellPctDamageModsDone /
# Unit::SpellHealingPctDone), so they are inert. Only eff1's own EffectSpellClassMaskA_2 (the Mass
# Dispel bit) is cleared, along with the effect it scoped. The rank-2 marker is read by icon 2210
# (unique to Focused Power inside the priest family) from Priest::ApplySpellTakenCritChanceMods.
_FOCUSED_POWER_NOTE = (
    'Discipline rework (5,0): Mass Dispel cast-time clause removed (eff1 + its classmask cleared); '
    '+2/4% damage and healing kept in their stock slots; rank 2 eff1 is now the Prayer of Healing '
    'crit capstone marker.'
)


focused_power_33186 = spell(
    id=33186,
    name='Focused Power',
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
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_HEALING_DONE_PERCENT, misc_value=127),
    ],
    spell_icon_id=2210,
    notes=_FOCUSED_POWER_NOTE,
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases damage and healing done by your spells by 2%.\n\n|cFF9D9D9DCapstone Bonus: Your Prayer of Healing has a 25% increased critical strike chance on targets affected by your Power Word: Shield, Greater Power Word: Shield, or Weakened Soul.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 8320, 'EffectSpellClassMaskB_2': 128, 'EffectSpellClassMaskC_2': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


focused_power_33190 = spell(
    id=33190,
    name='Focused Power',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        ApplyAura(AuraType.DUMMY, base_points=0, implicit_target_a=1),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.MOD_HEALING_DONE_PERCENT, misc_value=127),
    ],
    spell_icon_id=2210,
    notes=_FOCUSED_POWER_NOTE,
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases damage and healing done by your spells by 4%.\n\nCapstone Bonus: Your Prayer of Healing has a 25% increased critical strike chance on targets affected by your Power Word: Shield, Greater Power Word: Shield, or Weakened Soul.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 8320, 'EffectSpellClassMaskB_2': 128, 'EffectSpellClassMaskC_2': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


misery_33191 = spell(
    id=33191,
    name='Misery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=misery_33196.id),
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=108, misc_value=24),
    ],
    spell_icon_id=2211,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Shadow Word: Pain, Mind Flay and Vampiric Touch spells also increase the chance for harmful spells to hit by $33196s1% lasting $33196d, and increases the benefit from spell power gained by your Mind Blast, Mind Flay and Mind Sear spells by $s3%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 9469952, 'EffectSpellClassMaskB_1': 8421376, 'EffectSpellClassMaskB_2': 1024, 'EffectSpellClassMaskC_1': 8396800, 'EffectSpellClassMaskC_2': 524288, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 6},
)


misery_33192 = spell(
    id=33192,
    name='Misery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=33197),
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=24),
    ],
    spell_icon_id=2211,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Shadow Word: Pain, Mind Flay and Vampiric Touch spells also increase the chance for harmful spells to hit by $33197s1% lasting $33197d, and increases the benefit from spell power gained by your Mind Blast, Mind Flay and Mind Sear spells by $s3%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 9469952, 'EffectSpellClassMaskB_1': 8421376, 'EffectSpellClassMaskB_2': 1024, 'EffectSpellClassMaskC_1': 8396800, 'EffectSpellClassMaskC_2': 524288, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 6},
)


misery_33193 = spell(
    id=33193,
    name='Misery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=33198),
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108, misc_value=24),
    ],
    spell_icon_id=2211,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Shadow Word: Pain, Mind Flay and Vampiric Touch spells also increase the chance for harmful spells to hit by $33198s1% lasting $33198d, and increases the benefit from spell power gained by your Mind Blast, Mind Flay and Mind Sear spells by $s3%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 9469952, 'EffectSpellClassMaskB_1': 8421376, 'EffectSpellClassMaskB_2': 1024, 'EffectSpellClassMaskC_1': 8396800, 'EffectSpellClassMaskC_2': 524288, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 6},
)


# Priest Discipline rework (docs/reworks/priest-disc-rework.md (4,0)): reflected fraction retuned
# 22/45% -> 25/50% (stored 24/49, live-minus-1 per PLAN §3.5). The shape is unchanged - still the
# stock DUMMY/OVERRIDE_CLASS_SCRIPTS-style marker spell_pri_power_word_shield_aura's ReflectDamage
# path reads - which is also what makes it cover Greater Power Word: Shield (200155) for free, since
# that spell is bound to the same aura script. 33619 (the reflected-damage spell) already carries
# SPELL_ATTR1_NO_THREAT, so "causes no threat" needs no data change.
_REFLECTIVE_SHIELD_NOTE = 'Discipline rework (4,0): reflected fraction 22/45% -> 25/50%.'


reflective_shield_33201 = spell(
    id=33201,
    name='Reflective Shield',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=5065),
    ],
    spell_icon_id=566,
    notes=_REFLECTIVE_SHIELD_NOTE,
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes 25% of the damage you absorb with Power Word: Shield to reflect back at the attacker.  Calculated on the post-Mastery absorb value.  This damage causes no threat.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


reflective_shield_33202 = spell(
    id=33202,
    name='Reflective Shield',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=5064),
    ],
    spell_icon_id=566,
    notes=_REFLECTIVE_SHIELD_NOTE,
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes 50% of the damage you absorb with Power Word: Shield to reflect back at the attacker.  Calculated on the post-Mastery absorb value.  This damage causes no threat.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


focused_mind_33213 = spell(
    id=33213,
    name='Focused Mind',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-6, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=2014,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your Mind Blast, Mind Control, Mind Flay and Mind Sear spells by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 139264, 'EffectSpellClassMaskA_2': 1048576, 'EffectSpellClassMaskA_3': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


focused_mind_33214 = spell(
    id=33214,
    name='Focused Mind',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=2014,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your Mind Blast, Mind Control, Mind Flay and Mind Sear spells by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 139264, 'EffectSpellClassMaskA_2': 1048576, 'EffectSpellClassMaskA_3': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


focused_mind_33215 = spell(
    id=33215,
    name='Focused Mind',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-16, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=2014,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your Mind Blast, Mind Control, Mind Flay and Mind Sear spells by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 139264, 'EffectSpellClassMaskA_2': 1048576, 'EffectSpellClassMaskA_3': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


shadow_power_33221 = spell(
    id=33221,
    name='Shadow Power',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=2179,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of your Mind Blast, Mind Flay, and Shadow Word: Death spells by $s2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8192, 'EffectSpellClassMaskA_2': 2, 'EffectSpellClassMaskB_1': 8396800, 'EffectSpellClassMaskB_2': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


shadow_power_33222 = spell(
    id=33222,
    name='Shadow Power',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=2179,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of your Mind Blast, Mind Flay, and Shadow Word: Death spells by $s2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8192, 'EffectSpellClassMaskA_2': 2, 'EffectSpellClassMaskB_1': 8396800, 'EffectSpellClassMaskB_2': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


shadow_power_33223 = spell(
    id=33223,
    name='Shadow Power',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=59, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=2179,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of your Mind Blast, Mind Flay, and Shadow Word: Death spells by $s2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8192, 'EffectSpellClassMaskA_2': 2, 'EffectSpellClassMaskB_1': 8396800, 'EffectSpellClassMaskB_2': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


shadow_power_33224 = spell(
    id=33224,
    name='Shadow Power',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=79, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=2179,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of your Mind Blast, Mind Flay, and Shadow Word: Death spells by $s2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8192, 'EffectSpellClassMaskA_2': 2, 'EffectSpellClassMaskB_1': 8396800, 'EffectSpellClassMaskB_2': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


shadow_power_33225 = spell(
    id=33225,
    name='Shadow Power',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=2179,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of your Mind Blast, Mind Flay, and Shadow Word: Death spells by $s2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8192, 'EffectSpellClassMaskA_2': 2, 'EffectSpellClassMaskB_1': 8396800, 'EffectSpellClassMaskB_2': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


mind_melt_33371 = spell(
    id=33371,
    name='Mind Melt',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=107, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=3139,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Mind Blast, Mind Flay and Mind Sear spells by $s1%, and increases the periodic critical strike chance of your Vampiric Touch, Devouring Plague and Shadow Word: Pain spells by $s2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8396800, 'EffectSpellClassMaskA_2': 524288, 'EffectSpellClassMaskB_1': 33587200, 'EffectSpellClassMaskB_2': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


holy_concentration_34753 = spell(
    id=34753,
    name='Holy Concentration',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200199),
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2169,
    notes='Priest Holy rework (HOLY.md 6,0): reworked - eff1 now triggers the new 200199 Spirit buff '
          '(replacing the old mana-regen buff 34754); procs_on below adds Holy Fire/Smite crits to '
          'the trigger list (stock only covered heal crits). New eff2 DUMMY 33% (base_points=32) - '
          'the Renew-extension chance read by spell_pri_holy_concentration_extend.',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Spirit is increased by $200199s1% for $200199d after a critical heal with Flash Heal, Greater Heal or Binding Heal, or a critical hit with Holy Fire or Smite. Greater Heal, Flash Heal, Binding Heal and Circle of Healing have a $s2% chance to extend your Renew on all nearby party and raid members by 3 sec, to a maximum of 6 additional sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6, 'SpellLevel': 1, 'SpellPriority': 50},
)
procs_on(holy_concentration_34753, PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS | PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG,
         hit_mask=PROC_HIT_CRITICAL, family_name=6,
         family_mask=(_masks.FLASH_HEAL | _masks.GREATER_HEAL | _masks.SMITE | _masks.HOLY_FIRE, _masks.BINDING_HEAL, 0),
         chance=100)
# spell_pri_holy_concentration_extend binds on Greater Heal (2060), Flash Heal (2061), Binding
# Heal (32546) and Circle of Healing (34861) themselves (HOLY.md 6,0's Script column: AfterCast on
# each), not on this talent rank - see the scripted_by() calls next to those four spells in
# priest_spells.py.


holy_concentration_34859 = spell(
    id=34859,
    name='Holy Concentration',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200200),
        Effect(type=EffectType.APPLY_AURA, base_points=65, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2169,
    notes='Priest Holy rework (HOLY.md 6,0): rank 2 - triggers 200200 (20% Spirit); Renew-extension '
          'chance 66% (base_points=65).',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Spirit is increased by $200200s1% for $200200d after a critical heal with Flash Heal, Greater Heal or Binding Heal, or a critical hit with Holy Fire or Smite. Greater Heal, Flash Heal, Binding Heal and Circle of Healing have a $s2% chance to extend your Renew on all nearby party and raid members by 3 sec, to a maximum of 6 additional sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 131072, 'SpellClassSet': 6, 'SpellLevel': 1, 'SpellPriority': 50},
)
procs_on(holy_concentration_34859, PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS | PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG,
         hit_mask=PROC_HIT_CRITICAL, family_name=6,
         family_mask=(_masks.FLASH_HEAL | _masks.GREATER_HEAL | _masks.SMITE | _masks.HOLY_FIRE, _masks.BINDING_HEAL, 0),
         chance=100)


holy_concentration_34860 = spell(
    id=34860,
    name='Holy Concentration',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200201),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2169,
    notes='Priest Holy rework (HOLY.md 6,0): rank 3 - triggers 200201 (30% Spirit); Renew-extension '
          'chance 100% (base_points=99).',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Spirit is increased by $200201s1% for $200201d after a critical heal with Flash Heal, Greater Heal or Binding Heal, or a critical hit with Holy Fire or Smite. Greater Heal, Flash Heal, Binding Heal and Circle of Healing have a $s2% chance to extend your Renew on all nearby party and raid members by 3 sec, to a maximum of 6 additional sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 131072, 'SpellClassSet': 6, 'SpellLevel': 1, 'SpellPriority': 50},
)
procs_on(holy_concentration_34860, PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS | PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG,
         hit_mask=PROC_HIT_CRITICAL, family_name=6,
         family_mask=(_masks.FLASH_HEAL | _masks.GREATER_HEAL | _masks.SMITE | _masks.HOLY_FIRE, _masks.BINDING_HEAL, 0),
         chance=100)


# Priest Discipline rework (docs/reworks/priest-disc-rework.md (5,2)): Enlightenment now grants all
# three of the spec's stats at 1/2/3% - Spirit (eff1, MOD_TOTAL_STAT_PERCENTAGE misc 4), generalized
# haste (eff2, SPELL_AURA_MELEE_SLOW 193 = cast + ranged + melee in one effect, replacing the stock
# cast-only aura 65, per PLAN §1), and Intellect (eff3, MOD_TOTAL_STAT_PERCENTAGE misc 3, filling
# the previously-empty slot). NOTE the stock rows stored 1/3/5, i.e. live 2/4/6% (base_points is
# live-minus-1, PLAN §3.5) - DISC.md's table describes them as "1/2/3", which is the DESIGN DOC's
# number, not the stored one, so this is a real retune of Spirit/haste from 2/4/6% down to the
# spec's 1/2/3%, not a no-op. The stock EffectSpellClassMask* bytes are dropped: none of these
# three auras is a SpellMod, so AC never consults a classmask for them. The stock
# EffectBasePoints_3/EffectDieSides_3 raw_overrides are dropped too - raw_overrides is applied AFTER
# the effects list, so leaving them would clobber the new eff3.
_ENLIGHTENMENT_NOTE = (
    'Discipline rework (5,2): Spirit + generalized haste (aura 193) + Intellect, all 1/2/3% per '
    'the design doc (stock was 2/4/6% Spirit and cast-only haste).'
)


enlightenment_34908 = spell(
    id=34908,
    name='Enlightenment',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=4),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=3),
    ],
    spell_icon_id=2121,
    notes=_ENLIGHTENMENT_NOTE,
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Spirit, Intellect and spell, ranged and melee haste by 1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


enlightenment_34909 = spell(
    id=34909,
    name='Enlightenment',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=4),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=3),
    ],
    spell_icon_id=2121,
    notes=_ENLIGHTENMENT_NOTE,
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Spirit, Intellect and spell, ranged and melee haste by 2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


enlightenment_34910 = spell(
    id=34910,
    name='Enlightenment',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=4),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=3),
    ],
    spell_icon_id=2121,
    notes=_ENLIGHTENMENT_NOTE,
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Spirit, Intellect and spell, ranged and melee haste by 3%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


# Priest Discipline rework (docs/reworks/priest-disc-rework.md (7,2)): the single SPELLMOD_COOLDOWN
# effect keeps its stock dword-2 scope (EffectSpellClassMaskA_2 = 1887436800 = Inner Focus | Power
# Infusion | Pain Suppression | Penance) and gains a dword-3 one for the three custom spells the
# spec adds to the list - Leap of Faith (200137), Power Word: Barrier (200132) and Spirit Shell
# (200166), whose family bits are named in _masks.py per PLAN §4.4. The stock
# EffectSpellClassMaskB_1 = 576 is dropped: it scoped an effect 2 this spell does not have.
# Rank 2 also carries the capstone text; the capstone itself is pure C++
# (spell_pri_aspiration_power_infusion on 10060 - no new spell, PLAN §1).
_ASPIRATION_NOTE = (
    'Discipline rework (7,2): cooldown SpellMod extended with the Leap of Faith / Power Word: '
    'Barrier / Spirit Shell dword-3 bits; stray effect-2 classmask dropped; rank 2 carries the '
    'Power Infusion capstone line.'
)
_ASPIRATION_MASK_3 = _masks.LEAP_OF_FAITH | _masks.PW_BARRIER | _masks.SPIRIT_SHELL


aspiration_47507 = spell(
    id=47507,
    name='Aspiration',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COOLDOWN),
    ],
    spell_icon_id=2821,
    notes=_ASPIRATION_NOTE,
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Inner Focus, Power Infusion, Pain Suppression, Leap of Faith, Power Word: Barrier, Spirit Shell and Penance spells by 10%.\n\n|cFF9D9D9DCapstone Bonus: Casting Power Infusion on an ally also applies Power Infusion to you.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 1887436800, 'EffectSpellClassMaskA_3': _ASPIRATION_MASK_3, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


aspiration_47508 = spell(
    id=47508,
    name='Aspiration',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COOLDOWN),
    ],
    spell_icon_id=2821,
    notes=_ASPIRATION_NOTE,
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Inner Focus, Power Infusion, Pain Suppression, Leap of Faith, Power Word: Barrier, Spirit Shell and Penance spells by 20%.\n\nCapstone Bonus: Casting Power Infusion on an ally also applies Power Infusion to you.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 1887436800, 'EffectSpellClassMaskA_3': _ASPIRATION_MASK_3, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


# Priest Discipline rework (docs/reworks/priest-disc-rework.md (8,0)): trimmed to 2 ranks (47515 is
# orphaned by priest_talents.py and left as untouched pulled data) and retuned 10/20/30% -> 15/30%.
# Rank 2 gains a second DUMMY as the Mastery capstone marker; spell_pri_divine_aegis reads the
# rank amount from EFFECT_0 and the capstone from rank 2's own aura. The absorb spell 47753's
# duration drops 12 s -> 6 s (see its own row below), which is what the tooltips quote.
_DIVINE_AEGIS_NOTE = (
    'Discipline rework (8,0): 2 ranks at 15/30% (47515 orphaned); rank 2 eff2 is the Mastery '
    'capstone marker. Overheal/single-target/cap math lives in spell_pri_divine_aegis.'
)


divine_aegis_47509 = spell(
    id=47509,
    name='Divine Aegis',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        ApplyAura(AuraType.DUMMY, base_points=14, implicit_target_a=1),
    ],
    spell_icon_id=2820,
    notes=_DIVINE_AEGIS_NOTE,
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your critical Holy healing spells create a protective barrier absorbing damage up to 15% of the healed amount for $47753d.  Divine Aegis is doubled for single target heals.  Overhealing generates 75% less shielding, and the absorb is limited to 30% of the target's maximum health.\n\n|cFF9D9D9DCapstone Bonus: Your Divine Aegis absorption is additionally increased by your Mastery. This bonus is multiplicative and applies after all other modifiers.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 16384, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


divine_aegis_47511 = spell(
    id=47511,
    name='Divine Aegis',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        ApplyAura(AuraType.DUMMY, base_points=29, implicit_target_a=1),
        ApplyAura(AuraType.DUMMY, base_points=0, implicit_target_a=1),
    ],
    spell_icon_id=2820,
    notes=_DIVINE_AEGIS_NOTE,
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your critical Holy healing spells create a protective barrier absorbing damage up to 30% of the healed amount for $47753d.  Divine Aegis is doubled for single target heals.  Overhealing generates 75% less shielding, and the absorb is limited to 30% of the target's maximum health.\n\nCapstone Bonus: Your Divine Aegis absorption is additionally increased by your Mastery. This bonus is multiplicative and applies after all other modifiers.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 16384, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


divine_aegis_47515 = spell(
    id=47515,
    name='Divine Aegis',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2820,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Critical heals create a protective shield on the target, absorbing $s1% of the amount healed. Lasts $47753d.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 17408, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


# Priest Discipline rework (docs/reworks/priest-disc-rework.md (8,2)): Grace becomes 3 ranks at
# 33/66/100% chance for a 1/2/3%-per-stack buff, and Power Word: Shield joins Flash Heal / Greater
# Heal / Penance as a trigger. Because each rank now grants a DIFFERENT buff strength, each rank
# triggers its own buff spell: r1 -> grace_buff_200164 (1%), r2 -> grace_buff_200165 (2%), r3
# (grace_200163, below) -> the stock 47930 (3%). The per-rank chance is carried by each row's own
# DBC ProcChance and read back through the spell_proc row's Chance=0 fallback in
# SpellMgr::LoadSpellProcs - see the -14531 comment for why the r1/r2 proc row has to be the
# negative whole-chain form. Forward references to 200164/200165 are written as bare ints because
# those rows are declared further down this same file (the "declared earlier in this file" rule
# only applies within a file - see source/classes/README.md).
_GRACE_RANK_NOTE = (
    'Discipline rework (8,2): 3 ranks at 33/66/100% chance, Power Word: Shield added to the '
    'trigger mask, and each rank now triggers its own 1/2/3%-per-stack buff spell.'
)
_GRACE_TRIGGER_MASK = (_masks.PWS | _masks.FLASH_HEAL | _masks.GREATER_HEAL, _masks.PENANCE_HEAL_BOLT, 0)


grace_47516 = spell(
    id=47516,
    name='Grace',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=21, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200164),
    ],
    spell_icon_id=2819,
    notes=_GRACE_RANK_NOTE,
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'CumulativeAura': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Flash Heal, Greater Heal, Penance and Power Word: Shield have a 33% chance to bless the target with Grace, increasing all healing received from you by 1%.  Stacks up to 3 times.  Lasts 12 sec.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': _GRACE_TRIGGER_MASK[0], 'EffectSpellClassMaskA_2': _GRACE_TRIGGER_MASK[1], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 33, 'ProcTypeMask': 16384, 'RangeIndex': 1, 'SpellClassSet': 6},
)


grace_47517 = spell(
    id=47517,
    name='Grace',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=21, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200165),
    ],
    spell_icon_id=2819,
    notes=_GRACE_RANK_NOTE,
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'CumulativeAura': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Flash Heal, Greater Heal, Penance and Power Word: Shield have a 66% chance to bless the target with Grace, increasing all healing received from you by 2%.  Stacks up to 3 times.  Lasts 12 sec.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': _GRACE_TRIGGER_MASK[0], 'EffectSpellClassMaskA_2': _GRACE_TRIGGER_MASK[1], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 66, 'ProcTypeMask': 16384, 'RangeIndex': 1, 'SpellClassSet': 6},
)
# Ranks 1-2 share one whole-chain spell_proc row (see the -14531 comment): Chance is left at 0 so
# LoadSpellProcs falls back to each rank's own DBC ProcChance (33 / 66). AttributesMask 2 =
# PROC_ATTR_TRIGGERED_CAN_PROC, kept from the stock row - Penance's heal bolts are triggered casts
# and would otherwise never proc Grace. Rank 3 (200163) is a brand-new spell outside this rank
# chain and carries its own positive row, declared with it below.
procs_on(-47516, proc_flags=PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS, family_name=6,
         family_mask=_GRACE_TRIGGER_MASK, spell_phase_mask=PROC_SPELL_PHASE_HIT,
         attributes_mask=PROC_ATTR_TRIGGERED_CAN_PROC, chance=0)


# Priest Discipline rework (docs/reworks/priest-disc-rework.md (7,1)): the only data-side change is
# eff2, the "chance to energize your shielded target" roll - the spec makes that clause
# unconditional, so every rank now stores 100%. Everything else about Rapture is engine-side and
# belongs to WP-B: the self-mana amounts (1/1.75/2.5%) are NOT expressible here - the stock engine
# derives them from eff1's amount with a per-rank +/-0.5 fudge keyed on the spell id
# (SpellAuras.cpp's SPELLFAMILY_PRIEST Power Word: Shield block), and they are non-integers - and
# the target's 1% mana / 8 rage / 16 energy plus the 5 s internal cooldown (stock: 12 s) are
# hardcoded there too. eff1 is therefore left at its stock amount as the rank marker the engine
# still keys on.
_RAPTURE_NOTE = (
    'Discipline rework (7,1): target-energize chance raised to 100% on every rank (the spec drops '
    'the roll). Self-mana 1/1.75/2.5%, the 1% / 8 rage / 16 energy target values and the 5 s ICD '
    'are all engine-side (WP-B) - not representable in this row.'
)


rapture_47535 = spell(
    id=47535,
    name='Rapture',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2894,
    notes=_RAPTURE_NOTE,
    raw_overrides={'AttributesEx3': 67108864, 'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When your Power Word: Shield is completely absorbed you are instantly energized with 1% of your total mana.  You also energize your shielded target with 1% total mana, 8 rage and 16 energy.  This effect can only occur once every 5 sec.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 64, 'EffectSpellClassMaskB_1': 1, 'EffectSpellClassMaskB_2': 16777216, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


rapture_47536 = spell(
    id=47536,
    name='Rapture',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2894,
    notes=_RAPTURE_NOTE,
    raw_overrides={'AttributesEx3': 67108864, 'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When your Power Word: Shield is completely absorbed you are instantly energized with 1.75% of your total mana.  You also energize your shielded target with 1% total mana, 8 rage and 16 energy.  This effect can only occur once every 5 sec.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 64, 'EffectSpellClassMaskB_1': 1, 'EffectSpellClassMaskB_2': 16777216, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 6144, 'SpellClassMask_2': 65536, 'SpellClassSet': 6},
)


rapture_47537 = spell(
    id=47537,
    name='Rapture',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2894,
    notes=_RAPTURE_NOTE,
    raw_overrides={'AttributesEx3': 67108864, 'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When your Power Word: Shield is completely absorbed you are instantly energized with 2.5% of your total mana.  You also energize your shielded target with 1% total mana, 8 rage and 16 energy.  This effect can only occur once every 5 sec.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 64, 'EffectSpellClassMaskB_1': 1, 'EffectSpellClassMaskB_2': 16777216, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


test_of_faith_47558 = spell(
    id=47558,
    name='Test of Faith',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=112, misc_value=21),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2844,
    notes='Priest Holy rework (HOLY.md 8,2): eff1 (healing ≤50% target, engine misc 21) unchanged - '
          "4% stays 4% (base_points=3). eff2 REPURPOSED from the old '1 extra Aegis/other-consumer "
          "marker' DUMMY into the new '+4% Smite/Holy Fire damage vs ≤50% targets' marker "
          '(base_points=3), read by Priest::ApplyDoneDamagePctMods.',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your healing by $s1% and your Smite and Holy Fire damage by $s2% on friendly or enemy targets at or below 50% health.\n\n|cFF9D9D9DCapstone Bonus: You take 10% less magic damage while casting Smite, Holy Fire, or any Priest healing spell.|r', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': 419700288, 'EffectSpellClassMaskA_2': 134283300, 'EffectSpellClassMaskA_3': 4100, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


test_of_faith_47559 = spell(
    id=47559,
    name='Test of Faith',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=112, misc_value=6935),
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2844,
    notes='Priest Holy rework (HOLY.md 8,2): rank 2, healing 8% unchanged; damage marker +8% '
          '(base_points=7).',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your healing by $s1% and your Smite and Holy Fire damage by $s2% on friendly or enemy targets at or below 50% health.\n\n|cFF9D9D9DCapstone Bonus: You take 10% less magic damage while casting Smite, Holy Fire, or any Priest healing spell.|r', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': 419700288, 'EffectSpellClassMaskA_2': 134283300, 'EffectSpellClassMaskA_3': 4100, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


test_of_faith_47560 = spell(
    id=47560,
    name='Test of Faith',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=112, misc_value=6918),
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2844,
    notes='Priest Holy rework (HOLY.md 8,2): rank 3 (final kept rank), healing 12% unchanged; damage '
          'marker +12% (base_points=11); new eff3 capstone marker (base_points=0, i.e. present/1 - '
          'read by Priest::ApplySpellDamageTakenPctMods, not a %-scaled value itself, the -10% is a '
          'fixed multiplier gated on this marker existing). Tooltip capstone line, final rank plain color.',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your healing by $s1% and your Smite and Holy Fire damage by $s2% on friendly or enemy targets at or below 50% health.\n\nCapstone Bonus: You take 10% less magic damage while casting Smite, Holy Fire, or any Priest healing spell.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': 419700288, 'EffectSpellClassMaskA_2': 134283300, 'EffectSpellClassMaskA_3': 4100, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


divine_providence_47562 = spell(
    id=47562,
    name='Divine Providence',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=108, misc_value=11),
    ],
    spell_icon_id=2845,
    notes="Priest Holy rework (HOLY.md 9,0): now 3 ranks (47566/47567 orphaned), moved from (9,1). "
          'eff1 (heal%, unchanged 3%) mask gains Greater Heal (dw1) and Penance heal bolt (dw2) - '
          "Divine Hymn's own dw3=4 bit was already present. eff2 (the periodic/DoT-style variant, "
          "dw3-only in the pulled data) mask gains the same new custom-spell bits. eff3 REPURPOSED "
          'from a Prayer of Mending cooldown reduction (dw2=32) into a Halo cooldown reduction '
          '(dw3=HALO) - the exact SpellMod op (COOLDOWN) is unchanged, only its scope moves; -10% '
          '(base_points=-11).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount healed by Holy Word: Serenity, Holy Word: Sanctify, Circle of Healing, Binding Heal, Holy Nova, Halo, Prayer of Healing, Greater Heal, Penance and Divine Star by $s1%, and reduces the cooldown of your Halo by $s3%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 402657792, 'EffectSpellClassMaskA_2': 65540, 'EffectSpellClassMaskA_3': 25362436, 'EffectSpellClassMaskB_3': 25362436, 'EffectSpellClassMaskC_3': _masks.HALO, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


divine_providence_47564 = spell(
    id=47564,
    name='Divine Providence',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=108, misc_value=11),
    ],
    spell_icon_id=2845,
    notes='Priest Holy rework (HOLY.md 9,0): rank 2 - heal 6% unchanged; Halo cooldown -20% '
          '(base_points=-21); same mask changes as rank 1.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount healed by Holy Word: Serenity, Holy Word: Sanctify, Circle of Healing, Binding Heal, Holy Nova, Halo, Prayer of Healing, Greater Heal, Penance and Divine Star by $s1%, and reduces the cooldown of your Halo by $s3%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 402657792, 'EffectSpellClassMaskA_2': 65540, 'EffectSpellClassMaskA_3': 25362436, 'EffectSpellClassMaskB_3': 25362436, 'EffectSpellClassMaskC_3': _masks.HALO, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


divine_providence_47565 = spell(
    id=47565,
    name='Divine Providence',
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
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=108, misc_value=11),
    ],
    spell_icon_id=2845,
    notes='Priest Holy rework (HOLY.md 9,0): rank 3 (now the final kept rank), heal 6%->9% '
          '(base_points 5->8); Halo cooldown -30% (base_points=-31); same mask changes as rank 1.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount healed by Holy Word: Serenity, Holy Word: Sanctify, Circle of Healing, Binding Heal, Holy Nova, Halo, Prayer of Healing, Greater Heal, Penance and Divine Star by $s1%, and reduces the cooldown of your Halo by $s3%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 402657792, 'EffectSpellClassMaskA_2': 65540, 'EffectSpellClassMaskA_3': 25362436, 'EffectSpellClassMaskB_3': 25362436, 'EffectSpellClassMaskC_3': _masks.HALO, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


divine_providence_47566 = spell(
    id=47566,
    name='Divine Providence',
    school=School.NORMAL,
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
        Effect(type=EffectType.APPLY_AURA, base_points=-25, implicit_target_a=1, apply_aura=108, misc_value=11),
    ],
    spell_icon_id=2845,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount healed by Circle of Healing, Binding Heal, Holy Nova, Prayer of Healing, Divine Hymn and Prayer of Mending by $s1%, and reduces the cooldown of your Prayer of Mending by $s3%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 402653696, 'EffectSpellClassMaskA_2': 4, 'EffectSpellClassMaskA_3': 4, 'EffectSpellClassMaskB_3': 4, 'EffectSpellClassMaskC_2': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


divine_providence_47567 = spell(
    id=47567,
    name='Divine Providence',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=108, misc_value=11),
    ],
    spell_icon_id=2845,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount healed by Circle of Healing, Binding Heal, Holy Nova, Prayer of Healing, Divine Hymn and Prayer of Mending by $s1%, and reduces the cooldown of your Prayer of Mending by $s3%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 402653696, 'EffectSpellClassMaskA_2': 4, 'EffectSpellClassMaskA_3': 4, 'EffectSpellClassMaskB_3': 4, 'EffectSpellClassMaskC_2': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 6},
)


improved_shadowform_47569 = spell(
    id=47569,
    name='Improved Shadowform',
    school=School.NORMAL,
    attributes=65984,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=34, implicit_target_a=1, apply_aura=149, misc_value=32),
    ],
    spell_icon_id=217,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Fade ability now has a $s1% chance to remove all movement impairing effects when used while in Shadowform, and reduces casting or channeling time lost when damaged by $s2% when casting any Shadow spell while in Shadowform.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 134217728, 'SpellClassSet': 6},
)


improved_shadowform_47570 = spell(
    id=47570,
    name='Improved Shadowform',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=69, implicit_target_a=1, apply_aura=149, misc_value=32),
    ],
    spell_icon_id=217,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Fade ability now has a $s1% chance to remove all movement impairing effects when used while in Shadowform, and reduces casting or channeling time lost when damaged by $s2% when casting any Shadow spell while in Shadowform.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 134217728, 'SpellClassSet': 6},
)


twisted_faith_47573 = spell(
    id=47573,
    name='Twisted Faith',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=174, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=112, misc_value=7377),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=175, misc_value=4),
    ],
    spell_icon_id=2848,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell power by $s1% of your total Spirit, and your damage done by your Mind Flay and Mind Blast is increased by $s2% if your target is afflicted by your Shadow Word: Pain.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 4, 'EffectMiscValueB_3': 4, 'EffectSpellClassMaskA_1': 1026, 'EffectSpellClassMaskA_2': 1, 'EffectSpellClassMaskB_1': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassSet': 6},
)


twisted_faith_47577 = spell(
    id=47577,
    name='Twisted Faith',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=174, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=112, misc_value=7377),
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=175, misc_value=4),
    ],
    spell_icon_id=2848,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell power by $s1% of your total Spirit, and your damage done by your Mind Flay and Mind Blast is increased by $s2% if your target is afflicted by your Shadow Word: Pain.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 4, 'EffectSpellClassMaskA_1': 1026, 'EffectSpellClassMaskA_2': 1, 'EffectSpellClassMaskB_1': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassSet': 6},
)


twisted_faith_47578 = spell(
    id=47578,
    name='Twisted Faith',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=174, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=112, misc_value=7377),
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=175, misc_value=4),
    ],
    spell_icon_id=2848,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell power by $s1% of your total Spirit, and your damage done by your Mind Flay and Mind Blast is increased by $s2% if your target is afflicted by your Shadow Word: Pain.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 4, 'EffectSpellClassMaskA_1': 1026, 'EffectSpellClassMaskA_2': 1, 'EffectSpellClassMaskB_1': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassSet': 6},
)


pain_and_suffering_47580 = spell(
    id=47580,
    name='Pain and Suffering',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=47948),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2874,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Mind Flay has a $h% chance to refresh the duration of your Shadow Word: Pain on the target, and reduces the damage you take from your own Shadow Word: Death by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 2, 'EffectSpellClassMaskB_2': 32785, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 33, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 6},
)


pain_and_suffering_47581 = spell(
    id=47581,
    name='Pain and Suffering',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=47948),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2874,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Mind Flay has a $h% chance to refresh the duration of your Shadow Word: Pain on the target, and reduces the damage you take from your own Shadow Word: Death by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 2, 'EffectSpellClassMaskB_2': 32785, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 66, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassMask_1': 8388608, 'SpellClassSet': 6},
)


pain_and_suffering_47582 = spell(
    id=47582,
    name='Pain and Suffering',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=47948),
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2874,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Mind Flay has a $h% chance to refresh the duration of your Shadow Word: Pain on the target, and reduces the damage you take from your own Shadow Word: Death by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 2, 'EffectSpellClassMaskB_2': 32785, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 6},
)


# Priest Discipline rework (docs/reworks/priest-disc-rework.md (0,2), .agents/plans/priest-rework/
# priest-rework.DISC.md): the stock talent's two SpellMod effects (eff1 SPELLMOD_DAMAGE, eff2
# SPELLMOD_DOT, both scoped to the instant-Holy/Shadow classmask Blizzard authored) are kept exactly
# as they are; a third effect is added - SPELL_AURA_MOD_SPELL_CRIT_CHANCE_SCHOOL (71) with
# EffectMiscValue = SPELL_SCHOOL_MASK_HOLY|SHADOW (34), 1/2/3/4/5% - for the spec's new "and their
# critical strike chance by 1/2/3/4/5%" clause. School-scoped (not a SpellMod), so it needs no
# EffectSpellClassMask of its own and deliberately covers every Holy/Shadow spell, per PLAN §1's
# generalized-stats row. Stored base_points are live-minus-1 (die_sides defaults to 1, PLAN §3.5).
_TWIN_DISCIPLINES_NOTE = (
    'Discipline rework (0,2): stock eff1/eff2 SpellMods untouched; eff3 added as a Holy|Shadow '
    'school crit-chance aura (71, misc 34) for the spec\'s new crit clause. "Rank N" NameSubtext '
    'stripped (PLAN §3.1/§3.2).'
)


twin_disciplines_47586 = spell(
    id=47586,
    name='Twin Disciplines',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.MOD_SPELL_CRIT_CHANCE_SCHOOL, misc_value=School.HOLY | School.SHADOW),
    ],
    spell_icon_id=2292,
    notes=_TWIN_DISCIPLINES_NOTE,
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage and healing done by your Shadow and Holy spells and abilities by 1% and their critical strike chance by 1%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2581594112, 'EffectSpellClassMaskA_2': 622610, 'EffectSpellClassMaskB_1': 35684416, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 4194304, 'SpellClassSet': 6},
)


twin_disciplines_47587 = spell(
    id=47587,
    name='Twin Disciplines',
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
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_SPELL_CRIT_CHANCE_SCHOOL, misc_value=School.HOLY | School.SHADOW),
    ],
    spell_icon_id=2292,
    notes=_TWIN_DISCIPLINES_NOTE,
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage and healing done by your Shadow and Holy spells and abilities by 2% and their critical strike chance by 2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2581594112, 'EffectSpellClassMaskA_2': 622610, 'EffectSpellClassMaskB_1': 35684416, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 4194304, 'SpellClassSet': 6},
)


twin_disciplines_47588 = spell(
    id=47588,
    name='Twin Disciplines',
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
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MOD_SPELL_CRIT_CHANCE_SCHOOL, misc_value=School.HOLY | School.SHADOW),
    ],
    spell_icon_id=2292,
    notes=_TWIN_DISCIPLINES_NOTE,
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage and healing done by your Shadow and Holy spells and abilities by 3% and their critical strike chance by 3%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2581594112, 'EffectSpellClassMaskA_2': 622610, 'EffectSpellClassMaskB_1': 35684416, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 4194304, 'SpellClassSet': 6},
)


twisted_faith_51166 = spell(
    id=51166,
    name='Twisted Faith',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=174, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=112, misc_value=7377),
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=175, misc_value=4),
    ],
    spell_icon_id=2848,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell power by $s1% of your total Spirit, and your damage done by your Mind Flay and Mind Blast is increased by $s2% if your target is afflicted by your Shadow Word: Pain.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 4, 'EffectSpellClassMaskA_1': 1026, 'EffectSpellClassMaskA_2': 1, 'EffectSpellClassMaskB_1': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassSet': 6},
)


twisted_faith_51167 = spell(
    id=51167,
    name='Twisted Faith',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=174, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=112, misc_value=7377),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=175, misc_value=4),
    ],
    spell_icon_id=2848,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell power by $s1% of your total Spirit, and your damage done by your Mind Flay and Mind Blast is increased by $s2% if your target is afflicted by your Shadow Word: Pain.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 4, 'EffectSpellClassMaskA_1': 1026, 'EffectSpellClassMaskA_2': 1, 'EffectSpellClassMaskB_1': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassSet': 6},
)


# Priest Discipline rework (docs/reworks/priest-disc-rework.md (9,1)): trimmed to 3 ranks (52799/
# 52800 orphaned by priest_talents.py) and retuned - eff1's displayed haste follows the buff rows'
# new 7/14/20%, eff2's PW:S healing-power scaling (a DUMMY read by spell_pri_power_word_shield_aura)
# goes 8/16/24% -> 13/26/40%. Stored base_points are live-minus-1 (PLAN §3.5).
_BORROWED_TIME_RANK_NOTE = (
    'Discipline rework (9,1): 3 ranks (52799/52800 orphaned); haste 7/14/20%, PW:S spell-power '
    'scaling 13/26/40%.'
)


borrowed_time_52795 = spell(
    id=52795,
    name='Borrowed Time',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=21, trigger_spell=59887),
        Effect(type=EffectType.APPLY_AURA, base_points=12, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=24),
    ],
    spell_icon_id=2899,
    notes=_BORROWED_TIME_RANK_NOTE,
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Grants 7% spell haste for 6 sec after casting Power Word: Shield.  Consumed by your next non-instant spell.  Increases the healing power scaling of your Power Word: Shield by 13%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskB_1': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 16384, 'RangeIndex': 1, 'SpellClassSet': 6},
)


borrowed_time_52797 = spell(
    id=52797,
    name='Borrowed Time',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=13, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=21, trigger_spell=59888),
        Effect(type=EffectType.APPLY_AURA, base_points=25, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=24),
    ],
    spell_icon_id=2899,
    notes=_BORROWED_TIME_RANK_NOTE,
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Grants 14% spell haste for 6 sec after casting Power Word: Shield.  Consumed by your next non-instant spell.  Increases the healing power scaling of your Power Word: Shield by 26%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskB_1': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 16384, 'RangeIndex': 1, 'SpellClassSet': 6},
)


borrowed_time_52798 = spell(
    id=52798,
    name='Borrowed Time',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=21, trigger_spell=59889),
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=24),
    ],
    spell_icon_id=2899,
    notes=_BORROWED_TIME_RANK_NOTE,
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Grants 20% spell haste for 6 sec after casting Power Word: Shield.  Consumed by your next non-instant spell.  Increases the healing power scaling of your Power Word: Shield by 40%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskB_1': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 16384, 'RangeIndex': 1, 'SpellClassSet': 6},
)


borrowed_time_52799 = spell(
    id=52799,
    name='Borrowed Time',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=21, trigger_spell=59890),
        Effect(type=EffectType.APPLY_AURA, base_points=31, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=24),
    ],
    spell_icon_id=2899,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Grants $s1% spell haste for your next spell after casting Power Word: Shield, and increases the amount absorbed by your Power Word: Shield equal to $s2% of your spell power.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskB_1': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 16384, 'RangeIndex': 1, 'SpellClassSet': 6},
)


borrowed_time_52800 = spell(
    id=52800,
    name='Borrowed Time',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=21, trigger_spell=59891),
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=24),
    ],
    spell_icon_id=2899,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Grants $s1% spell haste for your next spell after casting Power Word: Shield, and increases the amount absorbed by your Power Word: Shield equal to $s2% of your spell power.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskB_1': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 16384, 'RangeIndex': 1, 'SpellClassSet': 6},
)


twin_disciplines_52802 = spell(
    id=52802,
    name='Twin Disciplines',
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
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.MOD_SPELL_CRIT_CHANCE_SCHOOL, misc_value=School.HOLY | School.SHADOW),
    ],
    spell_icon_id=2292,
    notes=_TWIN_DISCIPLINES_NOTE,
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage and healing done by your Shadow and Holy spells and abilities by 4% and their critical strike chance by 4%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2581594112, 'EffectSpellClassMaskA_2': 622610, 'EffectSpellClassMaskB_1': 35684416, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 4194304, 'SpellClassSet': 6},
)


twin_disciplines_52803 = spell(
    id=52803,
    name='Twin Disciplines',
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
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.MOD_SPELL_CRIT_CHANCE_SCHOOL, misc_value=School.HOLY | School.SHADOW),
    ],
    spell_icon_id=2292,
    notes=_TWIN_DISCIPLINES_NOTE,
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage and healing done by your Shadow and Holy spells and abilities by 5% and their critical strike chance by 5%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2581594112, 'EffectSpellClassMaskA_2': 1146898, 'EffectSpellClassMaskB_1': 35684416, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 4194304, 'SpellClassSet': 6},
)


# Priest Discipline rework (docs/reworks/priest-disc-rework.md (7,0)): mechanically unchanged - eff1
# stays the stock OVERRIDE_CLASS_SCRIPTS 7997/7998 crit-on-Weakened-Soul clause (engine-side,
# moving into Priest::ApplySpellTakenCritChanceMods in WP-B) and eff2 stays the PW:S-cast proc that
# applies 63944. Only the per-rank ProcChance is raised 50 -> 100 (the spec has no chance clause on
# the damage-reduction half) and the tooltips are rewritten, with rank 2 carrying the Greater Power
# Word: Shield capstone. NOTE: the spec asks for "1/2% reduced damage for 30 sec", which a single
# shared buff spell (63944, one row for both ranks, -3% for 60 s) cannot express per rank; DISC.md
# says to keep the stock row, so the tooltip quotes 63944's own values via $63944s1/$63944d rather
# than inventing a second buff spell.
_RENEWED_HOPE_NOTE = (
    'Discipline rework (7,0): ProcChance 50 -> 100 on rank 1, tooltips rewritten, rank 2 carries '
    'the Greater Power Word: Shield capstone. Effects unchanged (63944 stays one shared buff).'
)


renewed_hope_57470 = spell(
    id=57470,
    name='Renewed Hope',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=112, misc_value=7997),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=63944),
    ],
    spell_icon_id=329,
    notes=_RENEWED_HOPE_NOTE + (
        ' Post-audit fixes (talent-tooltip-audit, 2026-09-21): EffectSpellClassMaskA_1 was 4096 '
        '(Greater Heal only) - missing Flash Heal (2048) despite the tooltip and PriestMechanics.cpp'
        "'s IsAffectedOnSpell() check both naming it; corrected to 6144. Dropped the "
        '"$57470s3 sec cooldown" clause - Effect_3 on this spell has a stored amount but no real '
        'EffectType (ghost data from the pulled retail row, never backed by any cooldown '
        'mechanism); it rendered a fabricated 15-second cooldown that does not exist.'
    ),
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical effect chance of your Flash Heal, Greater Heal and Penance (Heal) spells by 2% on targets afflicted by Weakened Soul.  Your Power Word: Shield target takes $63944s1% reduced damage for $63944d.\n\n|cFF9D9D9DCapstone Bonus: Your Penance bolts have a 5% chance to transform your next Power Word: Shield into Greater Power Word: Shield. Lasts 30 sec, does not stack, consumed on use.|r', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 6144, 'EffectSpellClassMaskA_2': 65536, 'EffectSpellClassMaskB_1': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 16384, 'RangeIndex': 1, 'SpellClassSet': 6},
)


renewed_hope_57472 = spell(
    id=57472,
    name='Renewed Hope',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=112, misc_value=7998),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200168),
    ],
    spell_icon_id=329,
    notes=_RENEWED_HOPE_NOTE + (
        ' Post-audit fixes (talent-tooltip-audit, 2026-09-21): same EffectSpellClassMaskA_1 fix and '
        'ghost-cooldown removal as 57470 (see its own notes). Also: 63944 is one shared row that '
        "can't express two different percentages, so rank 2's trigger_spell now points at a new "
        'renewed_hope_target_debuff_200168 (a clone of 63944 at -2%/30s vs. 63944 retuned to '
        '-1%/30s) instead of both ranks sharing 63944 - see that row and 63944 for the full fix.'
    ),
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical effect chance of your Flash Heal, Greater Heal and Penance (Heal) spells by 4% on targets afflicted by Weakened Soul.  Your Power Word: Shield target takes $200168s1% reduced damage for $200168d.\n\nCapstone Bonus: Your Penance bolts have a 5% chance to transform your next Power Word: Shield into Greater Power Word: Shield. Lasts 30 sec, does not stack, consumed on use.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 6144, 'EffectSpellClassMaskA_2': 65536, 'EffectSpellClassMaskB_1': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 16384, 'RangeIndex': 1, 'SpellClassSet': 6},
)


# Priest Discipline rework (docs/reworks/priest-disc-rework.md (6,2)): eff1's stock
# SPELL_AURA_DUMMY with EffectMiscValue 7997 (the "+3/7/11% crit on friendly targets at or below
# 50% health" clause) is replaced by a plain SPELLMOD_CRITICAL_CHANCE modifier at +5/10/15%,
# unconditional. That clause was almost certainly dead code already: Unit.cpp's only 7997 handler
# is the OVERRIDE_CLASS_SCRIPTS path Renewed Hope uses (Unit.cpp:9075), which never sees a *dummy*
# 7997. eff1's classmask is re-scoped from the stock leftovers (4096 Greater Heal | 65536 Penance
# heal bolt, inherited from whatever row this was copied from) to just FLASH_HEAL on its own letter
# (A); eff2's cost modifier keeps its own correct EffectSpellClassMaskB_1 = FLASH_HEAL. Rank 3
# carries the Inner Focus cooldown capstone (spell_pri_improved_flash_heal_capstone, on 2061).
_IMPROVED_FLASH_HEAL_NOTE = (
    'Discipline rework (6,2): eff1 dummy-7997 clause replaced by an unconditional +5/10/15% '
    'SPELLMOD_CRITICAL_CHANCE scoped to Flash Heal; rank 3 gains the Inner Focus cooldown capstone.'
)


improved_flash_heal_63504 = spell(
    id=63504,
    name='Improved Flash Heal',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CRITICAL_CHANCE),
        Effect(type=EffectType.APPLY_AURA, base_points=-6, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COST),
    ],
    spell_icon_id=2542,
    notes=_IMPROVED_FLASH_HEAL_NOTE,
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your Flash Heal by 5%, and increases its critical effect chance by 5%.\n\n|cFF9D9D9DCapstone Bonus: Flash Heal casts reduce the cooldown of Inner Focus by 1 sec.|r', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': _masks.FLASH_HEAL, 'EffectSpellClassMaskB_1': _masks.FLASH_HEAL, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


improved_flash_heal_63505 = spell(
    id=63505,
    name='Improved Flash Heal',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CRITICAL_CHANCE),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COST),
    ],
    spell_icon_id=2542,
    notes=_IMPROVED_FLASH_HEAL_NOTE,
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your Flash Heal by 10%, and increases its critical effect chance by 10%.\n\n|cFF9D9D9DCapstone Bonus: Flash Heal casts reduce the cooldown of Inner Focus by 1 sec.|r', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': _masks.FLASH_HEAL, 'EffectSpellClassMaskB_1': _masks.FLASH_HEAL, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


improved_flash_heal_63506 = spell(
    id=63506,
    name='Improved Flash Heal',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CRITICAL_CHANCE),
        Effect(type=EffectType.APPLY_AURA, base_points=-16, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COST),
    ],
    spell_icon_id=2542,
    notes=_IMPROVED_FLASH_HEAL_NOTE,
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your Flash Heal by 15%, and increases its critical effect chance by 15%.\n\nCapstone Bonus: Flash Heal casts reduce the cooldown of Inner Focus by 1 sec.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': _masks.FLASH_HEAL, 'EffectSpellClassMaskB_1': _masks.FLASH_HEAL, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


empowered_renew_63534 = spell(
    id=63534,
    name='Empowered Renew',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=108, misc_value=24),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=7997),
    ],
    spell_icon_id=3021,
    notes='Priest Holy rework (HOLY.md 8,0): 5/10/15% -> 8/16/25% (rank 1: base_points 4->7). Instant'
          "chunk is rank-3-only now (design doc row 8,0's capstone): eff2's amount zeroed here "
          '(base_points=-1, i.e. 0% - the marker is still present so the spell keeps its effect '
          'count/shape, but rank 1/2 grant no instant chunk).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Renew spell gains an additional $s1% of your bonus healing effects.\n\n|cFF9D9D9DCapstone Bonus: Renew instantly heals for 25% of its total periodic effect on application. Each Renew critical tick extends its duration 1 sec, drawing on the shared extension pool.|r', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 64, 'EffectSpellClassMaskB_1': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


empowered_renew_63542 = spell(
    id=63542,
    name='Empowered Renew',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=108, misc_value=24),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=7997),
    ],
    spell_icon_id=3021,
    notes='Priest Holy rework (HOLY.md 8,0): rank 2, 16% (base_points=15). No instant chunk (see rank 1).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Renew spell gains an additional $s1% of your bonus healing effects.\n\n|cFF9D9D9DCapstone Bonus: Renew instantly heals for 25% of its total periodic effect on application. Each Renew critical tick extends its duration 1 sec, drawing on the shared extension pool.|r', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 64, 'EffectSpellClassMaskB_1': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


empowered_renew_63543 = spell(
    id=63543,
    name='Empowered Renew',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=108, misc_value=24),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=7997),
    ],
    spell_icon_id=3021,
    notes='Priest Holy rework (HOLY.md 8,0): rank 3 (final kept rank), 25% (base_points=24) plus the '
          'capstone: Renew instantly heals for 25% of its total periodic effect on application '
          '(eff2 DUMMY, base_points=24, read by the stock spell_pri_renew::HandleApplyEffect - only '
          'this rank carries a nonzero eff2, so the instant-chunk-on-apply behavior is rank-3-only '
          'by construction) plus a critical-tick duration-extend (procs_on + '
          'spell_pri_empowered_renew_capstone below). Tooltip capstone line, final rank plain color.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Renew spell gains an additional $s1% of your bonus healing effects.\n\nCapstone Bonus: Renew instantly heals for 25% of its total periodic effect on application. Each Renew critical tick extends its duration 1 sec, drawing on the shared extension pool.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 64, 'EffectSpellClassMaskB_1': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)
procs_on(empowered_renew_63543, PROC_FLAG_DONE_PERIODIC, hit_mask=PROC_HIT_CRITICAL,
         family_name=6, family_mask=(_masks.RENEW, 0, 0), chance=100)
scripted_by(empowered_renew_63543, 'spell_pri_empowered_renew_capstone')


# Priest Discipline rework (docs/reworks/priest-disc-rework.md (4,2)): Soul Warding becomes a
# 2-rank talent. This stock row is now RANK 1 (-2 sec / -7%, down from the stock single rank's
# -4 sec / -15%); rank 2 is the new soul_warding_200154 below, which carries the old values. Both
# effects keep their own correctly-lettered classmask (A for effect 1, B for effect 2) scoped to
# Power Word: Shield. The Power Word: Shield base cooldown is 4 sec (priest_spells.py's
# power_word_shield_17), so 2/2 takes it to 0.
_SOUL_WARDING_NOTE = (
    'Discipline rework (4,2): now 2 ranks - this row is rank 1 at -2 sec / -7% mana; rank 2 '
    '(200154) keeps the old -4 sec / -15%.'
)


soul_warding_63574 = spell(
    id=63574,
    name='Soul Warding',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-2001, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COOLDOWN),
        Effect(type=EffectType.APPLY_AURA, base_points=-8, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COST),
    ],
    spell_icon_id=2142,
    notes=_SOUL_WARDING_NOTE,
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Power Word: Shield by 2 sec, and reduces its mana cost by 7%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': _masks.PWS, 'EffectSpellClassMaskB_1': _masks.PWS, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


improved_devouring_plague_63625 = spell(
    id=63625,
    name='Improved Devouring Plague',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=27),
    ],
    spell_icon_id=3790,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the periodic damage done by your Devouring Plague by $s1%, and when you cast Devouring Plague you instantly deal damage equal to $s2% of its total periodic effect.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 33554432, 'EffectSpellClassMaskB_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


improved_devouring_plague_63626 = spell(
    id=63626,
    name='Improved Devouring Plague',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=27),
    ],
    spell_icon_id=3790,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the periodic damage done by your Devouring Plague by $s1%, and when you cast Devouring Plague you instantly deal damage equal to $s2% of its total periodic effect.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 33554432, 'EffectSpellClassMaskB_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


improved_devouring_plague_63627 = spell(
    id=63627,
    name='Improved Devouring Plague',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=27),
    ],
    spell_icon_id=3790,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the periodic damage done by your Devouring Plague by $s1%, and when you cast Devouring Plague you instantly deal damage equal to $s2% of its total periodic effect.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 33554432, 'EffectSpellClassMaskB_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)


serendipity_63730 = spell(
    id=63730,
    name='Serendipity',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=8152, trigger_spell=63731),
    ],
    spell_icon_id=2900,
    notes='Priest Holy rework (HOLY.md 7,2): rank 1 - procs_on below replaces the stock ProcTypeMask '
          'with NO family restriction (Classless: Paladin heals must also be able to charge this), '
          'the actual gating (Priest BH/FH/Renew/Smite vs Paladin Holy Light/Flash of Light) is '
          'done in spell_pri_serendipity\'s own CheckProc. Non-final-rank grey capstone preview '
          '(PLAN §3.1).',
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you heal with Binding Heal or Flash Heal, casting Renew, or damaging with Smite, the cast time and mana cost of your next Greater Heal or Prayer of Healing spell is reduced by $63731s1%. Stacks up to 3 times. Lasts $63731d.\n\n|cFF9D9D9DCapstone Bonus: Casting Greater Heal, Flash Heal, Binding Heal, Prayer of Healing, Circle of Healing, Renew, Smite or Holy Fire reduces the cooldown of your Holy Words.|r', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 6144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)
procs_on(serendipity_63730, PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS | PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG,
         spell_phase_mask=PROC_SPELL_PHASE_HIT | PROC_SPELL_PHASE_CAST, chance=100)
scripted_by(serendipity_63730, 'spell_pri_serendipity')


serendipity_63733 = spell(
    id=63733,
    name='Serendipity',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=8152, trigger_spell=63735),
    ],
    spell_icon_id=2900,
    notes='Priest Holy rework (HOLY.md 7,2): rank 2. Non-final-rank grey capstone preview (PLAN §3.1).',
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you heal with Binding Heal or Flash Heal, casting Renew, or damaging with Smite, the cast time and mana cost of your next Greater Heal or Prayer of Healing spell is reduced by $63735s1%. Stacks up to 3 times. Lasts $63735d.\n\n|cFF9D9D9DCapstone Bonus: Casting Greater Heal, Flash Heal, Binding Heal, Prayer of Healing, Circle of Healing, Renew, Smite or Holy Fire reduces the cooldown of your Holy Words.|r', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 6144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)
procs_on(serendipity_63733, PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS | PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG,
         spell_phase_mask=PROC_SPELL_PHASE_HIT | PROC_SPELL_PHASE_CAST, chance=100)
scripted_by(serendipity_63733, 'spell_pri_serendipity')


serendipity_63737 = spell(
    id=63737,
    name='Serendipity',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=8152, trigger_spell=63734),
    ],
    spell_icon_id=2900,
    notes='Priest Holy rework (HOLY.md 7,2): rank 3 - carries the capstone Holy Word engine '
          '(spell_pri_holy_word_engine, see the scripted_by() calls next to greater_heal_2060/'
          'flash_heal_2061/binding_heal_32546/prayer_of_healing_596/circle_of_healing_34861/'
          'renew_139/smite_585/holy_fire_14914 in priest_spells.py). Tooltip capstone line - final '
          'rank, plain color (PLAN §3.1).',
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you heal with Binding Heal or Flash Heal, casting Renew, or damaging with Smite, the cast time and mana cost of your next Greater Heal or Prayer of Healing spell is reduced by $63734s1%. Stacks up to 3 times. Lasts $63734d.\n\nCapstone Bonus: Casting Greater Heal, Flash Heal, Binding Heal, Prayer of Healing, Circle of Healing, Renew, Smite or Holy Fire reduces the cooldown of your Holy Words.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 6144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)
procs_on(serendipity_63737, PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS | PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG,
         spell_phase_mask=PROC_SPELL_PHASE_HIT | PROC_SPELL_PHASE_CAST, chance=100)
scripted_by(serendipity_63737, 'spell_pri_serendipity')


body_and_soul_64127 = spell(
    id=64127,
    name='Body and Soul',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=64128),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2218,
    notes='Priest Holy rework (HOLY.md 7,0): full mechanic replacement - eff1 now procs on casting '
          'Renew or Leap of Faith (procs_on below, family_mask RENEW dw1 + LEAP_OF_FAITH dw3) '
          'instead of Power Word: Shield; speed bonus unchanged (30% - PLAN §2 default, base_points '
          'stays 29). eff2 (the old "chance to also cleanse a poison" DUMMY) neutered to an inert '
          '0%-chance marker per the design doc\'s "drop the poison-cure clause" (D + script trim) - '
          'kept present, not removed, so the stock spell_pri_body_and_soul script\'s hook '
          'registration on this effect index does not break; the script body itself (WP-B) simply '
          'stops acting on it.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Casting Renew or Leap of Faith increases the target's movement speed by $s1% for $64128d.", 'EffectBasePoints_3': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)
procs_on(body_and_soul_64127, PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS, spell_phase_mask=PROC_SPELL_PHASE_CAST,
         family_name=6, family_mask=(_masks.RENEW, 0, _masks.LEAP_OF_FAITH), chance=100)


body_and_soul_64129 = spell(
    id=64129,
    name='Body and Soul',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=59, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=65081),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2218,
    notes='Priest Holy rework (HOLY.md 7,0): rank 2, 60% speed (base_points=59, unchanged). '
          "trigger_spell 65081 is now declared (talent-tooltip-audit fix, WP-C - was undeclared, "
          "which left this rank's own tooltip borrowing rank 1's $64128d token instead of its own "
          '$65081d); duration token corrected to match.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Casting Renew or Leap of Faith increases the target's movement speed by $s1% for $65081d.", 'EffectBasePoints_3': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6},
)
procs_on(body_and_soul_64129, PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS, spell_phase_mask=PROC_SPELL_PHASE_CAST,
         family_name=6, family_mask=(_masks.RENEW, 0, _masks.LEAP_OF_FAITH), chance=100)
scripted_by(body_and_soul_64129, 'spell_pri_body_and_soul')


# Priest baseline rework (docs/reworks/priest-new-spells.md) - Phase 1 shared spells. See
# priest_spells.py's own header comment for the 6 player-cast button spells this file's rows below
# are triggered by. Style/field-shape precedent throughout: Frost Mage's Frozen Orb Pulse
# (mage_trigger_spells.py's frozen_orb_pulse_200008 + spell_mage.cpp's spell_mage_frozen_orb) - the
# closest in-repo analog for a "summon a trigger NPC/aura that casts an owner-attributed pulse
# spell" mechanic.

angelic_feather_place_200141 = spell(
    id=200141,
    name='Angelic Feather',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=0,
    range_yards=40.0,
    effects=[
        Effect(type=104, implicit_target_a=87, misc_value=300101, radius_yards=2.0),
    ],
    spell_icon_id=90100,
    notes='Angelic Feather\'s actual GO-placement half, split out of angelic_feather_200130 (priest_spells.py - see that row\'s own notes for the full ring-investigation writeup and why this split exists). Never player-cast or spellbook-visible (no scripted_by/skill_line_ability/trained_by - same "hidden implementation spell" shape as this file\'s other trigger-only rows) - triggered once per cast of 200130 via that spell\'s own effect 2 (SPELL_EFFECT_TRIGGER_SPELL, Spell::EffectTriggerSpell in SpellEffects.cpp). This is the entirety of what the ORIGINAL single-spell 200130 used to carry as its own second effect before the split: SUMMON_OBJECT_SLOT1 (type 104, same effect type this project\'s pulled Hunter trap data already uses, e.g. Freezing Trap/1499), TARGET_DEST_DEST (implicit_target_a=87, same reticle mechanism Death and Decay uses), summoning gameobject_template entry 300101 (Angelic Feather trap GO). Targets=64 (raw_overrides below) is what makes SpellInfo::GetExplicitTargetMask() include TARGET_FLAG_DEST_LOCATION for this spell specifically (also already implied by effect 0\'s own ImplicitTargetA=87, independent of this override, but kept explicit to match the original single-spell row\'s own convention) - EffectTriggerSpell\'s SPELL_EFFECT_HANDLE_LAUNCH branch reads exactly that flag (`spellInfo->GetExplicitTargetMask() & TARGET_FLAG_DEST_LOCATION`) on *this* (triggered) spell to decide whether to copy the outer cast\'s ground-click destination down via `targets.SetDst(m_targets)` before casting this spell - without it, the feather would summon at the caster\'s own position instead of the clicked location. No mana_cost/cooldown_ms/duration_ms here: the outer spell (200130) already pays the real mana cost and owns the real 30-sec cooldown, and this spell is always triggered with TRIGGERED_FULL_MASK (ignores power/reagent cost and spell/category cooldowns regardless), and has no aura effect that would need a duration. spell_pri_angelic_feather\'s "only 3 feathers at once" BeforeCast hook (spell_priest_new.cpp) stays registered on 200130, not this spell - it is cast-level (not keyed to a SpellEffIndex) and 200130\'s BeforeCast still fires before 200130\'s own effect-handling (where the TRIGGER_SPELL effect that summons this spell\'s cast lives), so despawn-oldest-if-at-cap still correctly runs before the new feather is placed. No C++ changes needed for the split.',
    raw_overrides={'Targets': 64, 'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellClassSet': 6, 'SpellPriority': 50, 'SpellClassMask_3': _masks.ANGELIC_FEATHER},
)


angelic_feather_buff_200131 = spell(
    id=200131,
    name='Angelic Feather',
    school=School.HOLY,
    cast_time_ms=0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=21, apply_aura=AuraType.MOD_INCREASE_SPEED),
    ],
    spell_icon_id=90100,
    notes='Angelic Feather\'s triggered speed buff (docs/reworks/priest-new-spells.md, "grants 40% increased movement speed for 5 sec"). Cast by the Angelic Feather trap GameObject directly on whichever player triggers it - GameObject::CastSpell(target, trap.spellId) (GameObject.cpp:799) passes the found player as the explicit unit target, so implicit_target_a=21 (TARGET_UNIT_TARGET_ALLY) is what actually restricts the speed boost to allies: the trap itself fires on any nearby player, ally or enemy (native GAMEOBJECT_TYPE_TRAP "environmental trap" branch, GameObject.cpp:717-726 - trap.autoCloseTime=-1 takes AnyPlayerInObjectRangeCheck rather than the hostile-only hunter-trap NearestAttackableNoTotemUnitInObjectRangeCheck branch), so an enemy can trigger/consume a feather but this effect simply fails its own ally check against them. base_points=39 (this repo\'s stored-value-is-live-minus-1 convention, die_sides defaults to 1) for the tooltip\'s +40%. spell_icon_id 505 (Spell_Magic_FeatherFall) is a stock placeholder pending the icon-mining pass (see apps/dbc-tools/build_patch_i.py) which reuses this same value for the parent cast spell (angelic_feather_200130, priest_spells.py).',
    raw_overrides={'SpellClassSet': 0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 0, 'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Movement speed increased by 40%.', 'EquippedItemClass': -1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellPriority': 50},
)


divine_star_pulse_200134 = spell(
    id=200134,
    name='Divine Star',
    school=School.HOLY,
    cast_time_ms=0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=99, implicit_target_a=21),
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=99, implicit_target_a=6),
    ],
    spell_icon_id=90101,
    coeff_weight=0.4,
    notes='Divine Star\'s heal/damage pulse (docs/reworks/priest-new-spells.md: "100 (0.4 spellpower coeff) healing/damage"). Cast by the owning priest directly at whichever specific unit npc_pri_divine_star (spell_priest_new.cpp) finds newly within its own small pulse radius as it travels out and back - an explicit single-unit target per cast (owner->CastSpell(unit, 200134, true)), not a native AoE dest-area query. TARGET_UNIT_TARGET_ALLY (21) on the heal effect and TARGET_UNIT_TARGET_ENEMY (6) on the damage effect do NOT independently no-op against an explicit single-unit target server-side - Spell::SelectImplicitTargetObjectTargets (the TARGET_REFERENCE_TYPE_TARGET/TARGET_SELECT_CATEGORY_DEFAULT path these two target types take) never consults SpellImplicitTargetInfo::GetCheckType() the way the AoE/nearby/chain/trajectory search paths do, so both effects were applying to literally every unit hit - a priest healing themselves also silently self-damaged for the same amount, and any enemy hit also got healed. Playtest bugfix (2026-09-20, "not sure if Divine Star is healing, is it being attributed correctly"): spell_pri_divine_star_pulse (spell_priest_new.cpp) now hooks OnObjectTargetSelect per effect (EFFECT_0/ally, EFFECT_1/enemy) and nulls the target WorldObject*& when the caster\'s actual IsValidAssistTarget/IsValidAttackTarget disagrees with that effect\'s intended reaction - same idiom as spell_mage_arcane_blast::ClearSelfTarget (spell_mage.cpp) for nulling a single effect\'s target without touching the other effect\'s own resolution. This also gives full manual control over per-leg hit-dedup (tracked in the creature AI, not this row) rather than fighting native AoE re-hit semantics. base_points=99 (stored -1 convention) for the tooltip\'s 100; coeff_weight=0.4 matches the design doc\'s spellpower coefficient but is passthrough metadata only (lib/build.py\'s own docstring) - it never turns into a spell_bonus_data row or an EffectBonusMultiplier by itself. Confirmed live: spell_bonus_data had zero rows for 200134 and EffectBonusMultiplier_1/_2 were both 0 in spell_dbc, so every cast landed for a flat, non-scaling 100 regardless of the caster\'s spellpower. Fixed below via bonus_coefficients(), the actual mechanism (see halo_pulse_200136\'s own identical fix just above, and mage_trigger_spells.py/mage_spells.py for the established precedent - e.g. meteor_impact_200096, burnout_explosion_200116) that emits the spell_bonus_data row SpellMgr::GetSpellBonusData reads (both SpellDamageBonusDone and SpellHealingBonusDone key off the same direct_bonus column, so one row covers both effects). "Healing reduced beyond 6 targets": npc_pri_divine_star tracks a cast-wide (both legs) count of distinct allies healed and, once that count exceeds 6, casts the heal via CastCustomSpell/SPELLVALUE_BASE_POINT0 with a reduced amount instead of this row\'s own base_points - default falloff 10% per target beyond 6, compounding (retail\'s own value; docs/reworks/priest-new-spells.md doesn\'t specify a curve, flagged as playtest-tunable). No RangeIndex/range concern: the owner casts this triggered (bypasses range checks) at the missile\'s live position, which may be well outside the caster\'s own melee range. SpellVisualID_1=90013 is the yellow burst impact kit patch_priest_vfx_models.py mints (ChestEffect -> Priest_DivineStar_Impact_Yellow, mined from Ascension\'s client) - the missile\'s own travelling orb model is wired separately, on the creature_template row, not here.',
    raw_overrides={'SpellClassSet': 6, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 0, 'EquippedItemClass': -1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellPriority': 50, 'SpellVisualID_1': 90013, 'SpellClassMask_3': _masks.DIVINE_STAR},
)
scripted_by(divine_star_pulse_200134, 'spell_pri_divine_star_pulse')
bonus_coefficients(divine_star_pulse_200134, direct=0.4,
    comment='Divine Star pulse (200134) - 0.4 SP coeff on both the heal and the damage effect, docs/reworks/priest-new-spells.md')


halo_pulse_200136 = spell(
    id=200136,
    name='Halo',
    school=School.HOLY,
    cast_time_ms=0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=199, implicit_target_a=21),
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=199, implicit_target_a=6),
    ],
    spell_icon_id=90102,
    coeff_weight=0.526,
    notes='Halo\'s heal/damage pulse (docs/reworks/priest-new-spells.md: "200 (0.526 spellpower coeff) healing/damage"). Cast by the owning priest directly at whichever specific unit spell_pri_halo (AuraScript on 200135, spell_priest_new.cpp) finds newly crossed by the expanding ring on each periodic tick - same explicit-single-unit-target "ally heals / enemy damages" idiom as Divine Star\'s pulse (200134, priest_trigger_spells.py); see that spell\'s own notes for why this sidesteps native-AoE re-hit dedup problems entirely. base_points=199 (stored -1 convention) for the tooltip\'s 200; coeff_weight=0.526 matches the design doc. Playtest bugfix (2026-09-20, "Halo is also not healing either or its not being attributed correctly") - two independent bugs, same shape as Divine Star\'s own pulse (200134, see its notes just above for the full mechanism writeup): (1) TARGET_UNIT_TARGET_ALLY (21, EFFECT_0/HEAL) and TARGET_UNIT_TARGET_ENEMY (6, EFFECT_1/SCHOOL_DAMAGE) do NOT independently gate against an explicit single-unit target - Spell::SelectImplicitTargetObjectTargets never consults each effect\'s own check type for this target-reference path, so both effects landed on every unit the ring touched regardless of reaction (an ally took damage alongside the heal; an enemy got healed alongside the damage) - fixed by spell_pri_halo_pulse (spell_priest_new.cpp), same OnObjectTargetSelect-nulling idiom as spell_pri_divine_star_pulse. (2) coeff_weight alone is passthrough metadata only (lib/build.py\'s own docstring) - it never turns into a spell_bonus_data row or an EffectBonusMultiplier by itself, unlike what its name suggests. Confirmed live: spell_bonus_data had zero rows for 200136 and EffectBonusMultiplier_1/_2 were both 0 in spell_dbc, so every cast landed for a flat, non-scaling ~200 regardless of the caster\'s spellpower. Fixed by calling bonus_coefficients() below, the actual mechanism (see mage_trigger_spells.py/mage_spells.py for the established precedent - e.g. meteor_impact_200096, burnout_explosion_200116) that emits the spell_bonus_data row SpellMgr::GetSpellBonusData reads.',
    raw_overrides={'SpellClassSet': 6, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 0, 'EquippedItemClass': -1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellPriority': 50, 'SpellClassMask_3': _masks.HALO},
)
scripted_by(halo_pulse_200136, 'spell_pri_halo_pulse')
bonus_coefficients(halo_pulse_200136, direct=0.526,
    comment='Halo pulse (200136) - 0.526 SP coeff on both the heal and the damage effect, docs/reworks/priest-new-spells.md')


leap_of_faith_jump_200138 = spell(
    id=200138,
    name='Leap of Faith',
    school=School.HOLY,
    cast_time_ms=0,
    effects=[
        Effect(type=42, implicit_target_a=87),
    ],
    spell_icon_id=90103,
    notes='Leap of Faith\'s landing effect - SPELL_EFFECT_JUMP_DEST (type 42), TARGET_DEST_DEST (87, "the explicit dest this cast was given"). Mirrors DK Death Grip\'s own jump spell (57604, source/spells/npc.csv, pulled-from-client data) field-for-field, a known-working spline-jump in this exact engine build: base_points left unset (stored -1 convention -> live 0, matching 57604\'s own -1), Speed=50000.0 and EffectMiscValueB_1=150 copied verbatim from 57604\'s raw_overrides rather than guessed. spell_pri_leap_of_faith (spell_priest_new.cpp) casts this on the pulled ally at a point near the caster - target->CastSpell(destX, destY, destZ, 200138, true), same call shape as spell_dk_death_grip::HandleDummy\'s target->CastSpell(gripPos..., 57604, true) - direction reversed from Death Grip (the destination is near the *caster*, pulling the ally to the priest, not the other way around), so they land offset rather than stacked exactly on top of the caster.',
    raw_overrides={'SpellClassSet': 6, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 0, 'EquippedItemClass': -1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellPriority': 50, 'Speed': 50000.0, 'EffectMiscValueB_1': 150, 'Targets': 64, 'SpellClassMask_3': _masks.LEAP_OF_FAITH},
)


void_eruption_buff_200140 = spell(
    id=200140,
    name='Voidform',
    school=School.SHADOW,
    cast_time_ms=0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=90104,
    notes='Void Eruption\'s self-buff (docs/reworks/priest-new-spells.md: "increases your periodic Shadow damage by 10% for 10 sec, with the duration increased by 0.5 sec for each enemy hit... the 0.5 sec per enemy hit extends the buff duration, not the percentage"). No native WotLK AuraType computes "+X% periodic damage done" - SPELL_AURA_DUMMY (marker-aura-by-icon idiom, .claude/skills/class-rework Phase 3) read by Priest::ApplyDoneDamagePctMods (PriestMechanics.cpp) via caster->GetAuraEffect(SPELL_AURA_DUMMY, SPELLFAMILY_PRIEST, <this spell\'s own SpellIconID>, EFFECT_0). base_points=9 (stored -1 convention) for +10%. Reuses retail\'s own name for this buff ("Voidform") since the design doc doesn\'t name it, matching the mined icon (spell_priest_voidform.blp - no exact "voideruption" icon exists in the Ascension source archive; retail shares this icon between the spell and its buff anyway, see docs/ascension-asset-mining.md). Duration extension (+0.5s per enemy hit) is applied by spell_pri_void_eruption (spell_priest_new.cpp) via CastCustomSpell/SPELLVALUE_AURA_DURATION after counting hits, not expressible in this row\'s own static duration_ms (10000 here is the base/minimum, 0 enemies hit).',
    raw_overrides={'SpellClassSet': 0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Periodic Shadow damage increased by $s1%.', 'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Periodic Shadow damage increased by $s1%.', 'EquippedItemClass': -1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellPriority': 50},
)


divine_hymn_64844 = spell(
    id=64844,
    name='Divine Hymn',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    range_yards=40.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.HEAL, base_points=199, implicit_target_a=22, implicit_target_b=30, radius_yards=40.0),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=22, implicit_target_b=30, apply_aura=AuraType.MOD_HEALING_PCT, misc_value=127, radius_yards=40.0),
    ],
    spell_icon_id=2845,
    coeff_weight=0.2,
    notes='Priest baseline rework (docs/reworks/priest-new-spells.md): migrated out of the legacy source/spells/npc.csv (a pulled-from-client row; that row is deleted in the same change - generate.py would otherwise see this ID declared twice) into this DSL package so it can take coeff_weight/raw_overrides cleanly like every other spell here. implicit_target_a=22/implicit_target_b=30 (TARGET_UNIT_SRC_AREA_ALLY/TARGET_UNIT_PARTY, unchanged from the pulled data) - triggered every tick by 64843\'s own PERIODIC_TRIGGER_SPELL aura (priest_spells.py\'s divine_hymn_64843), cast by the priest each tick, landing on everyone within 40 yds. Old design capped this at the 3 lowest-health targets in spell_pri_divine_hymn::FilterTargets (spell_priest.cpp) - that resize(3) is deleted in the same change (its RaidCheck filter is kept); new design heals everyone in range. Retuned: 64843\'s own duration_ms 8000->5000 and amplitude 2000->1000 (5 ticks over 5 sec instead of 4 over 8), heal per tick ~200 (base_points=199, stored -1 convention; coeff_weight=0.2 reading the design doc\'s "1000 + 1.0 coeff over 5 sec" as a HoT-style total split evenly across 5 ticks, same convention as Renew\'s own tooltip math rather than a literal per-tick 1000 - flagged as a judgment call, revisit if it reads wrong in-game). Healing-taken buff, on this row\'s own APPLY_AURA effect: duration_ms 8000->15000 (this row\'s own duration governs the aura, independent of 64843\'s trigger cadence), 10%->4% per application (base_points 9->3, stored -1 convention), and CumulativeAura=5 added to raw_overrides so it stacks (the pulled data had none, meaning the old buff just refreshed at a flat 10% - default stack cap of 5 is a first-pass tunable, one full channel\'s worth of ticks, not specified in the design doc).',
    raw_overrides={'AttributesEx': 136, 'AttributesEx2': 1073741828, 'AttributesEx4': 128, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Healing received increased by $s2%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 0, 'EffectBonusMultiplier_1': 0.20000000298023224, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassMask_3': 4, 'SpellClassSet': 6, 'SpellVisualID_1': 13751, 'CumulativeAura': 5},
)


# --- Pulled from stock data via pull_dsl.py for the Disc pass (priest-rework.DISC.md WP-0
# step 1) - none of these are player-castable, all edited in place by WP-A. ---

# Priest Discipline rework (docs/reworks/priest-disc-rework.md (1,2), DISC.md's talent table):
# Martyrdom is rebuilt from "chance to gain Focused Casting after a melee/ranged crit" into "when
# you fall below 75% health, gain +5/10% healing done for 10 sec, at most once per 30 sec". The
# rank rows keep only a SPELL_AURA_DUMMY carrying the tuned percentage (read by
# spell_pri_martyrdom's OnProc, which casts martyrdom_buff_200145 with it as BP0); the old
# PROC_TRIGGER_SPELL -> 14743/27828 effect and the stock melee/ranged-crit ProcTypeMask (680) are
# gone - the trigger condition is now the spell_proc row below (PROC_FLAG_TAKEN_DAMAGE, 30 s ICD)
# plus the script's own "crossed the 75% threshold on this hit" CheckProc. Stored base_points are
# live-minus-1 (die_sides 1, PLAN §3.5).
_MARTYRDOM_NOTE = (
    'Discipline rework (1,2): reworked from Focused Casting to a below-75%-health healing buff. '
    'eff1 is now a DUMMY carrying the rank percentage; ProcTypeMask cleared, trigger moved to the '
    'spell_proc row (PROC_FLAG_TAKEN_DAMAGE, chance 100, 30 s cooldown) + spell_pri_martyrdom.'
)


martyrdom_14531 = spell(
    id=14531,
    name='Martyrdom',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        ApplyAura(AuraType.DUMMY, base_points=4, implicit_target_a=1),
    ],
    spell_icon_id=100,
    notes=_MARTYRDOM_NOTE,
    raw_overrides={'CastingTimeIndex': 1, 'ProcTypeMask': 0, 'ProcChance': 100, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you fall below 75% health, you gain Martyrdom, increasing your healing done by 5% for 10 sec.  Triggers on crossing the threshold and cannot occur more than once every 30 sec.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0},
)


martyrdom_14774 = spell(
    id=14774,
    name='Martyrdom',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        ApplyAura(AuraType.DUMMY, base_points=9, implicit_target_a=1),
    ],
    spell_icon_id=100,
    notes=_MARTYRDOM_NOTE,
    raw_overrides={'CastingTimeIndex': 1, 'ProcTypeMask': 0, 'ProcChance': 100, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you fall below 75% health, you gain Martyrdom, increasing your healing done by 10% for 10 sec.  Triggers on crossing the threshold and cannot occur more than once every 30 sec.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0},
)
scripted_by(martyrdom_14531, 'spell_pri_martyrdom')
scripted_by(martyrdom_14774, 'spell_pri_martyrdom')
# One spell_proc row for the whole rank chain, declared on the NEGATIVE first-rank id (-14531 =
# "this spell and every rank in its spell_ranks chain" - the same form the live stock row already
# uses, and the same form mage_trigger_spells.py's `procs_on(-44445, ...)` uses). This is load-
# bearing, not cosmetic: SpellMgr::LoadSpellProcs (SpellMgr.cpp) expands a negative row across the
# chain first (InnoDB returns the table in signed-PK order, so negatives are read before
# positives) and then rejects any later row for a spell already in the map with
# "has duplicate entry in the table". A pair of positive 14531/14774 rows would therefore be
# silently discarded while the stock -14531 row kept winning. Chance is given explicitly here, so
# the per-rank DBC ProcChance is not consulted.
procs_on(-14531, proc_flags=PROC_FLAG_TAKEN_DAMAGE, chance=100, cooldown_ms=30000)


# Priest Discipline rework (docs/reworks/priest-disc-rework.md (2,0)): the mana-regen-while-casting
# effect (SPELL_AURA_MOD_MANA_REGEN_INTERRUPT, 134) keeps its stock slot but is retuned to the
# spec's exact 16/33/50% - the stock rows stored 16/32/49, i.e. live 17/33/50 (base_points is
# live-minus-1 with die_sides 1, PLAN §3.5), so only rank 1 actually moves. Rank 3 additionally
# carries the capstone: SPELL_AURA_MOD_RATING_FROM_STAT (220) with EffectMiscValue = 1792
# (1<<CR_CRIT_MELEE | 1<<CR_CRIT_RANGED | 1<<CR_CRIT_SPELL - the generalized crit-rating mask from
# PLAN §1) and EffectMiscValueB_2 = 4 (STAT_SPIRIT), granting 15% of Spirit as crit rating.
_MEDITATION_NOTE = (
    'Discipline rework (2,0): retuned to the spec\'s 16/33/50% (stock stored values were live '
    '17/33/50); rank 3 gains the capstone MOD_RATING_FROM_STAT (220, misc 1792 = all three '
    'CR_CRIT_* bits, EffectMiscValueB_2 = STAT_SPIRIT) at 15% of Spirit.'
)


meditation_14521 = spell(
    id=14521,
    name='Meditation',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=AuraType.MOD_MANA_REGEN_INTERRUPT),
    ],
    spell_icon_id=44,
    notes=_MEDITATION_NOTE,
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Allows 16% of your mana regeneration to continue while casting.  Does not stack with other mana regeneration talents.\n\n|cFF9D9D9DCapstone Bonus: Your spell critical strike rating is increased by 15% of your Spirit.|r', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


meditation_14776 = spell(
    id=14776,
    name='Meditation',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=1, apply_aura=AuraType.MOD_MANA_REGEN_INTERRUPT),
    ],
    spell_icon_id=44,
    notes=_MEDITATION_NOTE,
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Allows 33% of your mana regeneration to continue while casting.  Does not stack with other mana regeneration talents.\n\n|cFF9D9D9DCapstone Bonus: Your spell critical strike rating is increased by 15% of your Spirit.|r', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


meditation_14777 = spell(
    id=14777,
    name='Meditation',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=AuraType.MOD_MANA_REGEN_INTERRUPT),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.MOD_RATING_FROM_STAT, misc_value=1792),
    ],
    spell_icon_id=44,
    notes=_MEDITATION_NOTE,
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_2': 4, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Allows 50% of your mana regeneration to continue while casting.  Does not stack with other mana regeneration talents.\n\nCapstone Bonus: Your spell critical strike rating is increased by 15% of your Spirit.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


# Priest Discipline rework (docs/reworks/priest-disc-rework.md (4,1)): Mental Strength goes from a
# 5-rank pure-Intellect talent to a 3-rank one with three effects - +3/6/10% Intellect
# (MOD_TOTAL_STAT_PERCENTAGE, misc 3 = STAT_INTELLECT), +2/4/6% of Intellect as crit rating
# (MOD_RATING_FROM_STAT 220, misc 1792 = the three CR_CRIT_* bits per PLAN §1, EffectMiscValueB_2 =
# 3 = STAT_INTELLECT), and -1/2/3% magic damage taken (MOD_DAMAGE_PERCENT_TAKEN 87, misc 126 = every
# school except Physical). Ranks 4-5 (18554/18555) are orphaned by priest_talents.py's 3-rank
# ranks=[...] and are deliberately left undeclared. Stored base_points are live-minus-1 (PLAN §3.5),
# which for the negative effect means live -1% -> stored -2.
_MENTAL_STRENGTH_NOTE = (
    'Discipline rework (4,1): trimmed to 3 ranks and rebuilt as Intellect % + crit-rating-from-'
    'Intellect + magic damage taken reduction. Ranks 18554/18555 orphaned.'
)


mental_strength_18551 = spell(
    id=18551,
    name='Mental Strength',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_RATING_FROM_STAT, misc_value=1792),
        Effect(type=EffectType.APPLY_AURA, base_points=-2, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
    ],
    spell_icon_id=139,
    notes=_MENTAL_STRENGTH_NOTE,
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_2': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Intellect by 3% and your critical strike rating by 2% of your Intellect.  Reduces all magic damage taken by 1%.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


mental_strength_18552 = spell(
    id=18552,
    name='Mental Strength',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.MOD_RATING_FROM_STAT, misc_value=1792),
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
    ],
    spell_icon_id=139,
    notes=_MENTAL_STRENGTH_NOTE,
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_2': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Intellect by 6% and your critical strike rating by 4% of your Intellect.  Reduces all magic damage taken by 2%.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


mental_strength_18553 = spell(
    id=18553,
    name='Mental Strength',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.MOD_RATING_FROM_STAT, misc_value=1792),
        Effect(type=EffectType.APPLY_AURA, base_points=-4, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
    ],
    spell_icon_id=139,
    notes=_MENTAL_STRENGTH_NOTE,
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_2': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Intellect by 10% and your critical strike rating by 6% of your Intellect.  Reduces all magic damage taken by 3%.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


# Priest Discipline rework (docs/reworks/priest-disc-rework.md (6,0)): the stock "after taking a
# critical hit you gain Focused Will" proc (eff1 PROC_TRIGGER_SPELL -> 45237/45241/45242) is cut
# entirely; the flat crit stays but moves from SPELL_AURA_MOD_SPELL_CRIT_CHANCE (57) to
# SPELL_AURA_MOD_CRIT_PCT (290, all crit - PLAN §1's generalized-stats row) at the same 1/2/3%.
# Rank 3 alone gains the capstone marker (eff1 DUMMY, amount 5 = the % chance) that
# spell_pri_focused_will's OnProc hangs off. Stock ProcTypeMask 139944 (the melee/ranged/spell
# taken-crit mask) is cleared - the trigger is now the spell_proc row below.
_FOCUSED_WILL_NOTE = (
    'Discipline rework (6,0): taken-crit proc removed, crit effect generalized to MOD_CRIT_PCT '
    '(290) at 1/2/3%, rank 3 gains the Empowered Penance capstone (DUMMY marker + spell_proc on '
    'Flash Heal/Greater Heal casts at 5%).'
)


focused_will_45234 = spell(
    id=45234,
    name='Focused Will',
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
        ApplyAura(AuraType.MOD_CRIT_PCT, base_points=0, implicit_target_a=1),
    ],
    spell_icon_id=2215,
    notes=_FOCUSED_WILL_NOTE,
    raw_overrides={'CastingTimeIndex': 1, 'ProcTypeMask': 0, 'ProcChance': 100, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell critical effect chance by 1%.\n\n|cFF9D9D9DCapstone Bonus: Your Flash Heal and Greater Heal have a 5% chance to empower your next Penance. Empowered Penance fires additional bolts at allies near your target, applying Divine Aegis to each. Lasts 30 sec, does not stack, consumed on use.|r', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0},
)


focused_will_45243 = spell(
    id=45243,
    name='Focused Will',
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
        ApplyAura(AuraType.MOD_CRIT_PCT, base_points=1, implicit_target_a=1),
    ],
    spell_icon_id=2215,
    notes=_FOCUSED_WILL_NOTE,
    raw_overrides={'CastingTimeIndex': 1, 'ProcTypeMask': 0, 'ProcChance': 100, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell critical effect chance by 2%.\n\n|cFF9D9D9DCapstone Bonus: Your Flash Heal and Greater Heal have a 5% chance to empower your next Penance. Empowered Penance fires additional bolts at allies near your target, applying Divine Aegis to each. Lasts 30 sec, does not stack, consumed on use.|r', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0},
)


focused_will_45244 = spell(
    id=45244,
    name='Focused Will',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        ApplyAura(AuraType.DUMMY, base_points=4, implicit_target_a=1),
        ApplyAura(AuraType.MOD_CRIT_PCT, base_points=2, implicit_target_a=1),
    ],
    spell_icon_id=2215,
    notes=_FOCUSED_WILL_NOTE,
    raw_overrides={'CastingTimeIndex': 1, 'ProcTypeMask': 0, 'ProcChance': 100, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell critical effect chance by 3%.\n\nCapstone Bonus: Your Flash Heal and Greater Heal have a 5% chance to empower your next Penance. Empowered Penance fires additional bolts at allies near your target, applying Divine Aegis to each. Lasts 30 sec, does not stack, consumed on use.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0},
)
scripted_by(focused_will_45244, 'spell_pri_focused_will')
# Negative (whole-rank-chain) spell_proc row - see the -14531 comment above for why a positive
# per-rank row would be silently dropped in favour of the live stock -45234 row. Ranks 1-2 do get
# the same proc entry as a side effect, but they carry no DUMMY effect and no script, so nothing
# happens for them. Phase CAST (not HIT): the capstone keys off casting Flash Heal/Greater Heal.
procs_on(-45234, proc_flags=PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS, family_name=6,
         family_mask=(_masks.FLASH_HEAL | _masks.GREATER_HEAL, 0, 0),
         spell_phase_mask=PROC_SPELL_PHASE_CAST, chance=5)


# Priest Discipline rework (docs/reworks/priest-disc-rework.md (9,1)): the three Borrowed Time
# haste buffs go from SPELL_AURA_MOD_CASTING_SPEED_NOT_STACK (65, cast haste only) to
# SPELL_AURA_MELEE_SLOW (193 - misnamed in the C++ enum; it is the generalized cast+melee+ranged
# haste aura Bloodlust itself uses, HandleModCombatSpeedPct above SpellAuraEffects.cpp:4762), per
# PLAN §1's generalized-stats row, and are retuned 5/10/15% -> 7/14/20% (stored 6/13/19, PLAN
# §3.5). EffectMiscValue is unused by that handler, so the stock 14 is dropped.
_BORROWED_TIME_BUFF_NOTE = (
    'Discipline rework (9,1): haste aura generalized 65 -> 193 (cast + melee + ranged) and '
    'retuned to 7/14/20%.'
)


borrowed_time_59887 = spell(
    id=59887,
    name='Borrowed Time',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL),
    ],
    spell_icon_id=2899,
    notes=_BORROWED_TIME_BUFF_NOTE,
    raw_overrides={'AttributesEx2': 4, 'AttributesEx4': 64, 'CastingTimeIndex': 1, 'ProcTypeMask': 81920, 'ProcChance': 100, 'ProcCharges': 1, 'BaseLevel': 10, 'SpellLevel': 10, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 6144, 'EffectSpellClassMaskA_2': 4, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'Grants spell haste for your next spell after casting Power Word: Shield.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '7% spell haste until next spell cast.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 6, 'SpellClassMask_3': 1056, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


borrowed_time_59888 = spell(
    id=59888,
    name='Borrowed Time',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=13, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL),
    ],
    spell_icon_id=2899,
    notes=_BORROWED_TIME_BUFF_NOTE,
    raw_overrides={'AttributesEx2': 4, 'AttributesEx4': 64, 'CastingTimeIndex': 1, 'ProcTypeMask': 81920, 'ProcChance': 100, 'ProcCharges': 1, 'BaseLevel': 10, 'SpellLevel': 10, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 6144, 'EffectSpellClassMaskA_2': 4, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'Grants spell haste for your next spell after casting Power Word: Shield.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '14% spell haste until next spell cast.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 6, 'SpellClassMask_3': 1056, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


borrowed_time_59889 = spell(
    id=59889,
    name='Borrowed Time',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL),
    ],
    spell_icon_id=2899,
    notes=_BORROWED_TIME_BUFF_NOTE,
    raw_overrides={'AttributesEx2': 4, 'AttributesEx4': 64, 'CastingTimeIndex': 1, 'ProcTypeMask': 81920, 'ProcChance': 100, 'ProcCharges': 1, 'BaseLevel': 10, 'SpellLevel': 10, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 6144, 'EffectSpellClassMaskA_2': 4, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'Grants spell haste for your next spell after casting Power Word: Shield.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '20% spell haste until next spell cast.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 6, 'SpellClassMask_3': 1056, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


grace_47930 = spell(
    id=47930,
    name='Grace',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=12000,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=21, apply_aura=AuraType.MOD_HEALING_RECEIVED),
    ],
    spell_icon_id=2819,
    notes='Discipline rework baseline edit (DISC.md "Baseline spell edits"): duration 15 s -> 12 s. Stays the 3%-per-stack, 3-stack buff and is now triggered only by Grace rank 3 (grace_200163); ranks 1-2 trigger the 1%/2% clones 200164/200165. The EffectSpellClassMaskB_* bytes are load-bearing and untouched: SPELL_AURA_MOD_HEALING_RECEIVED (283) is filtered through AuraEffect::IsAffectedOnSpell in Unit::SpellHealingBonusTaken, so those dwords are what restricts the bonus to the priest\'s own healing spells.',
    raw_overrides={'AttributesEx3': 262272, 'AttributesEx5': 32, 'AttributesEx7': 268435456, 'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'CumulativeAura': 3, 'EquippedItemClass': -1, 'EffectDieSides_1': 1, 'EffectBasePoints_1': -1, 'EffectSpellClassMaskA_1': 64, 'EffectSpellClassMaskB_1': 423894593, 'EffectSpellClassMaskB_2': 65572, 'EffectSpellClassMaskB_3': 2147500036, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_enUS': 'Increases all healing received from the Priest by 3%.  Stacks up to 3 times.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases all healing received by the Priest by $s2%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 6, 'SpellClassMask_2': 4096, 'SpellClassMask_3': 1024, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


renewed_hope_63944 = spell(
    id=63944,
    name='Renewed Hope',
    school=School.HOLY,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-2, implicit_target_a=21, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN),
    ],
    spell_icon_id=329,
    notes=(
        'Renewed Hope (7,0) rank 1\'s PW:S-target debuff. Post-audit fix (talent-tooltip-audit, '
        '2026-09-21): this row was pulled from existing data with apply_aura=DUMMY (4) and '
        'misc_value=8063 - grepping the whole engine for "8063" finds no handler anywhere, so the '
        '"reduced damage" this spell\'s own tooltip claimed never actually reduced anything; it was '
        'a cosmetic-only buff. Switched to MOD_DAMAGE_PERCENT_TAKEN (87, the same native aura Power '
        'Word: Barrier already uses for its own -20%) so the reduction is real with no C++ needed. '
        'Retuned to the design doc\'s 1% (stored -2, die_sides=1 default) / 30 sec (was a pulled-data '
        '-3%/60s that matched neither the doc\'s 1/2% nor 30 sec). Rank 2 gets its own row, '
        'renewed_hope_target_debuff_200168, since one shared buff spell cannot express two '
        'different percentages - see 57472 (rank 2) for why its trigger_spell points there instead '
        'of here. Review fix (disc-review-fixes, 2026-09-21): implicit_target_a was 56 '
        '(TARGET_UNIT_CASTER_AREA_RAID, radius 100) - a leftover from the pulled-data row - which '
        'buffed the whole raid on every Power Word: Shield cast regardless of Renewed Hope, making '
        'both this spell and the hand-applied cast on Greater PW:S extra targets '
        '(spell_pri_power_word_shield::HandleGreaterShield) pointless. 21 (TARGET_UNIT_TARGET_ALLY) '
        'matches the design doc ("Your Power Word: Shield target takes...reduced damage") and lets '
        '57470/57472\'s own PROC_TRIGGER_SPELL apply it to just the shield target.'
    ),
    raw_overrides={'AttributesEx2': 4, 'AttributesEx6': 67108864, 'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 6144, 'EffectSpellClassMaskA_2': 65536, 'EffectSpellClassMaskB_1': 1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'Increases the critical effect chance of your Flash Heal, Greater Heal and Penance (Heal) spells on targets afflicted by the Weakened Soul effect, and you have a chance to reduce damage taken by your Power Word: Shield target.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Reduces damage taken by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 6, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


renewed_hope_target_debuff_200168 = spell(
    id=200168,
    name='Renewed Hope',
    school=School.HOLY,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=21, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN),
    ],
    spell_icon_id=329,
    notes=(
        'Renewed Hope (7,0) rank 2\'s own PW:S-target debuff - a clone of 63944 (rank 1\'s row, see '
        'its notes) at 2% (stored -3) instead of 1%, minted from DISC.md\'s spare 200168-200171 '
        "block since a single shared buff spell can't hold two different percentages. Bound as "
        "57472's (rank 2) PROC_TRIGGER_SPELL trigger_spell in place of 63944. Review fix "
        "(disc-review-fixes, 2026-09-21): same implicit_target_a fix as 63944 (56/raid -> "
        "21/TARGET_UNIT_TARGET_ALLY) - see that row's notes for why."
    ),
    raw_overrides={'AttributesEx2': 4, 'AttributesEx6': 67108864, 'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 6144, 'EffectSpellClassMaskA_2': 65536, 'EffectSpellClassMaskB_1': 1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'Increases the critical effect chance of your Flash Heal, Greater Heal and Penance (Heal) spells on targets afflicted by the Weakened Soul effect, and you have a chance to reduce damage taken by your Power Word: Shield target.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Reduces damage taken by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 6, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


divine_aegis_47753 = spell(
    id=47753,
    name='Divine Aegis',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=21, apply_aura=AuraType.SCHOOL_ABSORB, misc_value=127),
    ],
    spell_icon_id=2820,
    notes='Discipline rework baseline edit (DISC.md "Baseline spell edits"): absorb duration 12 s -> 6 s. Nothing else changes - the amount is always supplied by spell_pri_divine_aegis via CastCustomSpell, never by this row\'s own base_points.',
    raw_overrides={'AttributesEx2': 2621440, 'AttributesEx3': 67108864, 'AttributesEx4': 1048576, 'CastingTimeIndex': 1, 'InterruptFlags': 8, 'ProcChance': 101, 'BaseLevel': 1, 'SpellLevel': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 10895, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Critical heals create a protective shield on the target, absorbing a percentage of the amount healed.  Lasts $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Absorbs damage.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 6, 'SpellClassMask_2': 16781312, 'SpellClassMask_3': 1024, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0},
)


rapture_47755 = spell(
    id=47755,
    name='Rapture',
    school=School.HOLY,
    attributes=671350784,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.ENERGIZE, implicit_target_a=1),
    ],
    spell_icon_id=2894,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 536870912, 'CastingTimeIndex': 1, 'BaseLevel': 1, 'SpellLevel': 1, 'DurationIndex': 0, 'EquippedItemClass': -1, 'SpellVisualID_1': 12495, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'When your Power Word: Shield is completely absorbed or dispelled you are instantly energized with 2.5% of your total mana, and you have a chance to energize your shielded target with $47537s1% total mana, $/10;63653s1 rage, $63655s1 energy or $/10;63652s1 runic power. This effect can only occur once every $63853d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


rapture_63654 = spell(
    id=63654,
    name='Rapture',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=134217728,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=EffectType.ENERGIZE, base_points=-1, implicit_target_a=21),
    ],
    spell_icon_id=2894,
    notes='pulled from existing data',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 60, 'SpellLevel': 60, 'DurationIndex': 0, 'EquippedItemClass': -1, 'SpellVisualID_1': 12489, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'When your Power Word: Shield is completely absorbed or dispelled you are instantly energized with 2.5% of your total mana, and you have a chance to energize your shielded target with $47537s1% total mana, $/10;63653s1 rage, $63655s1 energy or $/10;63652s1 runic power. This effect can only occur once every $63853d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


weakened_soul_6788 = spell(
    id=6788,
    name='Weakened Soul',
    school=2,
    mechanic=19,
    attributes=603979776,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=15000,
    effects=[
        Effect(type=6, die_sides=0, implicit_target_a=25, apply_aura=77, misc_value=19),
    ],
    spell_icon_id=177,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 196744, 'AttributesEx2': 4, 'CastingTimeIndex': 1, 'ProcChance': 101, 'EquippedItemClass': -1, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': "The target's soul is weakened by the force of Power Word: Shield, and cannot be shielded again for $d.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Cannot be affected by Power Word: Shield.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 6, 'SpellClassMask_1': 536870912, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


reflective_shield_33619 = spell(
    id=33619,
    name='Reflective Shield',
    school=2,
    attributes=134217728,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=-1,
    effects=[
        Effect(type=2, implicit_target_a=6),
    ],
    spell_icon_id=237,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 1160, 'AttributesEx2': 4, 'AttributesEx4': 16384, 'ShapeshiftExclude': 134217728, 'CastingTimeIndex': 1, 'ProcChance': 101, 'SpellLevel': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 8383, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Causes a percentage of the damage absorbed by your Power Word: Shield to reflect back at the attacker. This damage causes no threat.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 6, 'SpellClassMask_2': 16384, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


# =====================================================================================
# Priest Discipline rework - new hidden/trigger-only spells (spell block 200142-200167,
# pre-assigned in .agents/plans/priest-rework/priest-rework.DISC.md's "ID map").
#
# None of these is ever cast from a Spellbook - they are talent-rank passives, SpellMod
# buffs, absorb shells and "your next X is empowered" markers. The one player-castable
# new spell of this pass, Spirit Shell 200166, lives in priest_spells.py.
#
# Conventions used throughout (PLAN §3.5 / §3.1):
#   * base_points is the LIVE value minus 1 whenever die_sides is 1 (the default).
#     Rows whose amount is supplied at cast time by a script (CastCustomSpell with
#     SPELLVALUE_BASE_POINT0) instead set die_sides=0, so the engine does not silently
#     add 1 to the script's own number.
#   * every ADD_FLAT_MODIFIER/ADD_PCT_MODIFIER effect carries an
#     EffectSpellClassMask<letter>_<dword> on its OWN letter (A = effect 1, B = effect 2,
#     C = effect 3); an all-zero one would mean "every spell in the family".
#   * NameSubtext ("Rank N") is empty everywhere - ranks do not exist on this server.
# =====================================================================================

_DISC_PASSIVE_RAW = {
    'CastingTimeIndex': 1,
    'ProcChance': 101,
    'RangeIndex': 1,
    'EquippedItemClass': -1,
    'Name_Lang_Mask': 16712190,
    'NameSubtext_Lang_Mask': 16712190,
    'NameSubtext_Lang_enUS': '',
    'Description_Lang_Mask': 16712190,
    'AuraDescription_Lang_Mask': 16712188,
    'SpellClassSet': 6,
    'EffectChainAmplitude_1': 1.0,
    'EffectChainAmplitude_2': 1.0,
    'EffectChainAmplitude_3': 1.0,
}


def _passive_raw(**extra) -> dict:
    """Shared raw_overrides for a new Discipline talent-rank passive - the same column
    shape every stock priest talent rank row carries, so the generated rows look like
    their neighbours instead of like a half-filled template."""
    row = dict(_DISC_PASSIVE_RAW)
    row.update(extra)
    return row


# --- (1,0) Reprieve, talent 352 (was Silent Resolve) ---------------------------------
# Shortens Weakened Soul by 1/2/3 sec via a SPELLMOD_DURATION flat modifier scoped to
# Weakened Soul's own family bit. A flat-ms SpellMod stores live-minus-1 exactly like a
# percentage does (cf. Soul Warding's -2001 for -2000 ms). Rank 3 adds the capstone
# marker effect that spell_pri_reprieve's OnProc hangs off; the trigger itself is the
# spell_proc row below, on rank 3's id only.
_REPRIEVE_NOTE = (
    'Discipline rework (1,0) NEW, talent id 352 repurposed from Silent Resolve. '
    'SPELLMOD_DURATION -1/-2/-3 sec on Weakened Soul; rank 3 carries the '
    'Flash Heal / Greater Heal / Penance-bolt capstone (spell_pri_reprieve).'
)

reprieve_200142 = spell(
    id=200142,
    name='Reprieve',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1001, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.DURATION),
    ],
    spell_icon_id=177,
    notes=_REPRIEVE_NOTE,
    raw_overrides=_passive_raw(
        EffectSpellClassMaskA_1=_masks.WEAKENED_SOUL,
        Description_Lang_enUS='Reduces the duration of your Weakened Soul effect by 1 sec.\n\n|cFF9D9D9DCapstone Bonus: Flash Heal and each bolt of Penance reduce the remaining duration of Weakened Soul on the healed target by 0.5 sec. Greater Heal reduces it by 2 sec. Affects only the target you healed.|r',
    ),
)


reprieve_200143 = spell(
    id=200143,
    name='Reprieve',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-2001, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.DURATION),
    ],
    spell_icon_id=177,
    notes=_REPRIEVE_NOTE,
    raw_overrides=_passive_raw(
        EffectSpellClassMaskA_1=_masks.WEAKENED_SOUL,
        Description_Lang_enUS='Reduces the duration of your Weakened Soul effect by 2 sec.\n\n|cFF9D9D9DCapstone Bonus: Flash Heal and each bolt of Penance reduce the remaining duration of Weakened Soul on the healed target by 0.5 sec. Greater Heal reduces it by 2 sec. Affects only the target you healed.|r',
    ),
)


reprieve_200144 = spell(
    id=200144,
    name='Reprieve',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-3001, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.DURATION),
        ApplyAura(AuraType.DUMMY, base_points=0, implicit_target_a=1),
    ],
    spell_icon_id=177,
    notes=_REPRIEVE_NOTE,
    raw_overrides=_passive_raw(
        EffectSpellClassMaskA_1=_masks.WEAKENED_SOUL,
        ProcTypeMask=PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS,
        Description_Lang_enUS='Reduces the duration of your Weakened Soul effect by 3 sec.\n\nCapstone Bonus: Flash Heal and each bolt of Penance reduce the remaining duration of Weakened Soul on the healed target by 0.5 sec. Greater Heal reduces it by 2 sec. Affects only the target you healed.',
    ),
)
scripted_by(reprieve_200144, 'spell_pri_reprieve')
# AttributesMask 2 (PROC_ATTR_TRIGGERED_CAN_PROC) so Penance's triggered heal bolts count,
# same as Grace's own row. Phase HIT so eventInfo.GetProcTarget() is the healed unit.
procs_on(reprieve_200144, proc_flags=PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS, family_name=6,
         family_mask=(_masks.FLASH_HEAL | _masks.GREATER_HEAL, _masks.PENANCE_HEAL_BOLT, 0),
         spell_phase_mask=PROC_SPELL_PHASE_HIT,
         attributes_mask=PROC_ATTR_TRIGGERED_CAN_PROC, chance=100)


# --- (1,2) Martyrdom buff ------------------------------------------------------------
martyrdom_buff_200145 = spell(
    id=200145,
    name='Martyrdom',
    school=School.HOLY,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MOD_HEALING_DONE_PERCENT, misc_value=127),
    ],
    spell_icon_id=100,
    notes='Discipline rework (1,2): the buff spell_pri_martyrdom casts on the priest when they '
          'drop below 75% health. die_sides=0 because the amount always arrives as BP0 from '
          'CastCustomSpell (the talent rank\'s own DUMMY amount, 5 or 10) - with the default '
          'die_sides=1 the engine would silently add 1 to it.',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Healing done is increased.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Healing done is increased.', 'SpellClassSet': 6, 'SpellPriority': 50, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


# --- (2,1) Inner Focus: Mind Blast slow ----------------------------------------------
inner_focus_mind_blast_slow_200146 = spell(
    id=200146,
    name='Inner Focus',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    mechanic=Mechanic.SNARE,
    duration_ms=5000,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-71, mechanic=Mechanic.SNARE, implicit_target_a=6, apply_aura=AuraType.MOD_DECREASE_SPEED),
    ],
    spell_icon_id=101,
    notes='Discipline rework (2,1): the -70% movement-speed snare an Inner Focus-empowered Mind '
          'Blast applies to its target (spell_pri_inner_focus_mind_blast, a SpellScript on 8092, '
          'casts it AfterHit). base_points -71 = live -70% (PLAN §3.5). Mechanic SNARE on both the '
          'spell and the effect so it obeys the normal snare immunity/dispel rules.',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Movement speed slowed by 70%.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement speed slowed by 70%.', 'SpellClassSet': 6, 'DefenseType': 1, 'PreventionType': 1, 'SpellPriority': 50, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


# --- (2,3) Copious Power, talent 350 (was Improved Mana Burn) ------------------------
# Passive ranks proc off a Power Word: Shield cast and grant a 1-charge SpellMod buff that
# makes the next cast-time heal 5/10/15% stronger. The spell_proc rows mirror Borrowed
# Time's live row (same trigger spell, same phase): family 6, PW:S bit, phase HIT.
_COPIOUS_POWER_NOTE = (
    'Discipline rework (2,3) NEW, talent id 350 repurposed from Improved Mana Burn. '
    'PROC_TRIGGER_SPELL on Power Word: Shield -> a 1-charge SPELLMOD_DAMAGE buff '
    '(200150-200152) worth 5/10/15% on the next Flash Heal / Greater Heal / Prayer of '
    'Healing / Binding Heal.'
)
# Which heals the buff applies to. SPELLMOD_DAMAGE is the op AC runs healing through as
# well as damage (Unit::SpellHealingBonusDone, Unit.cpp:9511).
_COPIOUS_POWER_HEALS = (_masks.FLASH_HEAL | _masks.GREATER_HEAL | _masks.POH, _masks.BINDING_HEAL, 0)

copious_power_200147 = spell(
    id=200147,
    name='Copious Power',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200150),
    ],
    spell_icon_id=2170,
    notes=_COPIOUS_POWER_NOTE,
    raw_overrides=_passive_raw(
        ProcTypeMask=PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS,
        ProcChance=100,
        EffectSpellClassMaskA_1=_masks.PWS,
        Description_Lang_enUS='After casting Power Word: Shield your next healing spell with a cast time is 5% more effective.',
    ),
)
procs_on(copious_power_200147, proc_flags=PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS, family_name=6,
         family_mask=(_masks.PWS, 0, 0), spell_phase_mask=PROC_SPELL_PHASE_HIT, chance=100)


copious_power_200148 = spell(
    id=200148,
    name='Copious Power',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200151),
    ],
    spell_icon_id=2170,
    notes=_COPIOUS_POWER_NOTE,
    raw_overrides=_passive_raw(
        ProcTypeMask=PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS,
        ProcChance=100,
        EffectSpellClassMaskA_1=_masks.PWS,
        Description_Lang_enUS='After casting Power Word: Shield your next healing spell with a cast time is 10% more effective.',
    ),
)
procs_on(copious_power_200148, proc_flags=PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS, family_name=6,
         family_mask=(_masks.PWS, 0, 0), spell_phase_mask=PROC_SPELL_PHASE_HIT, chance=100)


copious_power_200149 = spell(
    id=200149,
    name='Copious Power',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200152),
    ],
    spell_icon_id=2170,
    notes=_COPIOUS_POWER_NOTE,
    raw_overrides=_passive_raw(
        ProcTypeMask=PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS,
        ProcChance=100,
        EffectSpellClassMaskA_1=_masks.PWS,
        Description_Lang_enUS='After casting Power Word: Shield your next healing spell with a cast time is 15% more effective.',
    ),
)
procs_on(copious_power_200149, proc_flags=PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS, family_name=6,
         family_mask=(_masks.PWS, 0, 0), spell_phase_mask=PROC_SPELL_PHASE_HIT, chance=100)


_COPIOUS_POWER_BUFF_NOTE = (
    'Discipline rework (2,3): the 1-charge SpellMod buff Copious Power grants. ProcCharges=1 with '
    'no ProcTypeMask - a SpellMod aura drops its charge through Player::ApplySpellMod when the '
    'modified spell is actually cast, not through the proc system.'
)

copious_power_buff_200150 = spell(
    id=200150,
    name='Copious Power',
    school=School.HOLY,
    attributes=327680,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=2170,
    notes=_COPIOUS_POWER_BUFF_NOTE,
    raw_overrides={'AttributesEx2': 4, 'CastingTimeIndex': 1, 'ProcChance': 101, 'ProcCharges': 1, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': _COPIOUS_POWER_HEALS[0], 'EffectSpellClassMaskA_2': _COPIOUS_POWER_HEALS[1], 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your next healing spell with a cast time is 5% more effective.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Next healing spell with a cast time is 5% more effective.', 'SpellClassSet': 6, 'DefenseType': 1, 'PreventionType': 1, 'SpellPriority': 50, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


copious_power_buff_200151 = spell(
    id=200151,
    name='Copious Power',
    school=School.HOLY,
    attributes=327680,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=2170,
    notes=_COPIOUS_POWER_BUFF_NOTE,
    raw_overrides={'AttributesEx2': 4, 'CastingTimeIndex': 1, 'ProcChance': 101, 'ProcCharges': 1, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': _COPIOUS_POWER_HEALS[0], 'EffectSpellClassMaskA_2': _COPIOUS_POWER_HEALS[1], 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your next healing spell with a cast time is 10% more effective.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Next healing spell with a cast time is 10% more effective.', 'SpellClassSet': 6, 'DefenseType': 1, 'PreventionType': 1, 'SpellPriority': 50, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


copious_power_buff_200152 = spell(
    id=200152,
    name='Copious Power',
    school=School.HOLY,
    attributes=327680,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=2170,
    notes=_COPIOUS_POWER_BUFF_NOTE,
    raw_overrides={'AttributesEx2': 4, 'CastingTimeIndex': 1, 'ProcChance': 101, 'ProcCharges': 1, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': _COPIOUS_POWER_HEALS[0], 'EffectSpellClassMaskA_2': _COPIOUS_POWER_HEALS[1], 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your next healing spell with a cast time is 15% more effective.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Next healing spell with a cast time is 15% more effective.', 'SpellClassSet': 6, 'DefenseType': 1, 'PreventionType': 1, 'SpellPriority': 50, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


# --- (3,0) Absolution buff ------------------------------------------------------------
absolution_buff_200153 = spell(
    id=200153,
    name='Absolution',
    school=School.HOLY,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_PCT),
    ],
    spell_icon_id=2212,
    notes='Discipline rework (3,0): the crit buff spell_pri_absolution grants after a successful '
          'magic dispel/purge. MOD_CRIT_PCT (290) is the generalized all-crit aura per PLAN §1. '
          'die_sides=0 - the amount is always BP0 from CastCustomSpell (8/16/25 from the talent '
          'rank\'s DUMMY).',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Critical strike chance is increased.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Critical strike chance is increased.', 'SpellClassSet': 6, 'SpellPriority': 50, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


# --- (4,2) Soul Warding rank 2 --------------------------------------------------------
soul_warding_200154 = spell(
    id=200154,
    name='Soul Warding',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-4001, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COOLDOWN),
        Effect(type=EffectType.APPLY_AURA, base_points=-16, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COST),
    ],
    spell_icon_id=2142,
    notes='Discipline rework (4,2) NEW rank 2 of Soul Warding - the stock row 63574 becomes rank 1 '
          '(-2 sec / -7%) and this carries the old -4 sec / -15%, taking Power Word: Shield\'s '
          '4 sec base cooldown to 0 at full rank.',
    raw_overrides=_passive_raw(
        EffectSpellClassMaskA_1=_masks.PWS,
        EffectSpellClassMaskB_1=_masks.PWS,
        Description_Lang_enUS='Reduces the cooldown of your Power Word: Shield by 4 sec, and reduces its mana cost by 15%.',
    ),
)


# --- (7,0) Greater Power Word: Shield -------------------------------------------------
# A clone of Power Word: Shield 17's absorb effect only: no Weakened Soul trigger, no mana
# cost, no cooldown, no SkillLineAbility row (never learned or cast from a Spellbook - it
# is cast for the caster by spell_pri_power_word_shield's AfterCast on the two extra
# targets). It carries ONLY dword-3 bit 22 (_masks.GREATER_PWS), deliberately NOT Power
# Word: Shield's own dword-1 bit, so Soul Warding / Borrowed Time / Copious Power / Grace
# do not see it as a second Power Word: Shield cast. Everything the spec DOES want on it
# - the shared CalculateAmount path, Reflective Shield, Focused Power's crit check, Grace
# and Renewed Hope on the extra targets - comes from the shared aura script instead.
greater_power_word_shield_200155 = spell(
    id=200155,
    name='Greater Power Word: Shield',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    mechanic=19,
    attributes=329728,
    range_yards=40.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=43, points_per_level=16.6296, implicit_target_a=21, apply_aura=AuraType.SCHOOL_ABSORB, misc_value=127),
    ],
    spell_icon_id=453,
    notes='Discipline rework: the secondary shield the Renewed Hope capstone puts on the 2 nearest '
          'injured allies (docs/reworks/priest-disc-rework.md, "Greater Power Word: Shield"). '
          'Effect/BasePoints/RealPointsPerLevel/AttributesEx2 copied verbatim from Power Word: '
          'Shield 17 so the base absorb matches; ExcludeTargetAuraSpell (Weakened Soul) is '
          'deliberately NOT copied - the extra shields do not apply or respect Weakened Soul. '
          'Icon 453 (Spell_Holy_BlessingOfProtection, stock) gives it a distinct icon from Power '
          'Word: Shield (566) rather than the shared/reused one it had before.',
    raw_overrides={'AttributesEx2': 2621440, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Absorbs damage.', 'BaseLevel': 1, 'SpellLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Draws on the soul of the friendly target to shield them, absorbing damage.  While the shield holds, spellcasting will not be interrupted by damage.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_3': _masks.GREATER_PWS, 'SpellClassSet': 6, 'SpellPriority': 50, 'SpellVisualID_1': 784},
)
scripted_by(greater_power_word_shield_200155, 'spell_pri_power_word_shield_aura')


# --- (5,3) Guiding Star, talent 342 (was Unbreakable Will) ----------------------------
# eff1 cuts Divine Star's cooldown, eff2 raises ONLY the pulse's heal half, eff3 is the
# absorb percentage spell_pri_divine_star_pulse reads.
#
# eff2 is SPELLMOD_EFFECT1, not SPELLMOD_DAMAGE, on purpose: divine_star_pulse_200134's
# Effect_1 is the HEAL and its Effect_2 is the SCHOOL_DAMAGE, so SPELLMOD_DAMAGE would
# buff the damage half too. Both SpellMods are scoped on dword 3 (_masks.DIVINE_STAR),
# each on its own letter - A for effect 1, B for effect 2.
_GUIDING_STAR_NOTE = (
    'Discipline rework (5,3) NEW, talent id 342 repurposed from Unbreakable Will. '
    '-15/30% Divine Star cooldown, +10/20% to its HEAL effect only (SPELLMOD_EFFECT1, since '
    'the pulse 200134 puts the heal on Effect_1 and the damage on Effect_2), and a DUMMY '
    'carrying the 15/30% absorb percentage spell_pri_divine_star_pulse applies via 200158.'
)

guiding_star_200156 = spell(
    id=200156,
    name='Guiding Star',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-16, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COOLDOWN),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.EFFECT1),
        ApplyAura(AuraType.DUMMY, base_points=14, implicit_target_a=1),
    ],
    spell_icon_id=2139,
    notes=_GUIDING_STAR_NOTE,
    raw_overrides=_passive_raw(
        EffectSpellClassMaskA_3=_masks.DIVINE_STAR,
        EffectSpellClassMaskB_3=_masks.DIVINE_STAR,
        Description_Lang_enUS='Increases the healing done by your Divine Star by 10%, reduces its cooldown by 15%, and causes its healing to apply an absorb shield equal to 15% of the amount healed.  Applies once per pass, so a full out-and-back cast shields twice.',
    ),
)


guiding_star_200157 = spell(
    id=200157,
    name='Guiding Star',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COOLDOWN),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.EFFECT1),
        ApplyAura(AuraType.DUMMY, base_points=29, implicit_target_a=1),
    ],
    spell_icon_id=2139,
    notes=_GUIDING_STAR_NOTE,
    raw_overrides=_passive_raw(
        EffectSpellClassMaskA_3=_masks.DIVINE_STAR,
        EffectSpellClassMaskB_3=_masks.DIVINE_STAR,
        Description_Lang_enUS='Increases the healing done by your Divine Star by 20%, reduces its cooldown by 30%, and causes its healing to apply an absorb shield equal to 30% of the amount healed.  Applies once per pass, so a full out-and-back cast shields twice.',
    ),
)


guiding_star_absorb_200158 = spell(
    id=200158,
    name='Guiding Star',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    range_yards=100.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, die_sides=0, implicit_target_a=21, apply_aura=AuraType.SCHOOL_ABSORB, misc_value=127),
    ],
    spell_icon_id=2139,
    notes='Discipline rework (5,3): the absorb shield Guiding Star puts on each ally Divine Star '
          'heals. Self-contained - it does NOT need the Divine Aegis talent and stacks with it '
          '(PLAN §2). Attribute set copied from Divine Aegis\' own absorb spell 47753 so it '
          'behaves identically as a shield; die_sides=0 because the amount always arrives as BP0 '
          'from CastCustomSpell.',
    raw_overrides={'AttributesEx2': 2621440, 'AttributesEx3': 67108864, 'AttributesEx4': 1048576, 'CastingTimeIndex': 1, 'InterruptFlags': 8, 'ProcChance': 101, 'BaseLevel': 1, 'SpellLevel': 1, 'EquippedItemClass': -1, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Absorbs damage.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Absorbs damage.', 'SpellClassSet': 6, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


# --- (6,0) Empowered Penance -----------------------------------------------------------
empowered_penance_ready_200159 = spell(
    id=200159,
    name='Empowered Penance',
    school=School.HOLY,
    duration_ms=30000,
    effects=[
        ApplyAura(AuraType.DUMMY, base_points=0, implicit_target_a=1),
    ],
    spell_icon_id=2215,
    notes='Discipline rework (6,0): the "your next Penance is empowered" marker the Focused Will '
          'capstone grants (spell_pri_focused_will). Does not stack; spell_pri_penance consumes it '
          'when the channel starts.',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your next Penance fires additional bolts at allies near your target.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next Penance fires additional bolts at allies near your target.', 'SpellClassSet': 6, 'SpellPriority': 50, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


penance_empowered_200160 = spell(
    id=200160,
    name='Penance',
    school=School.HOLY,
    attributes=65536,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=669, points_per_level=33.9167, die_sides=87, implicit_target_a=21),
    ],
    spell_icon_id=2818,
    notes='Discipline rework (6,0): the extra ally heal bolt Empowered Penance fires. A copy of the '
          'normal Penance heal bolt 47750\'s amount and 0.537 spell-power coefficient, single '
          'target. Deliberately carries NO SpellFamilyFlags bits: it must not itself proc Grace / '
          'Reprieve / Renewed Hope a second time on top of the real bolt that spawned it.',
    raw_overrides={'AttributesEx2': 4194308, 'AttributesEx3': 512, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EffectBonusMultiplier_1': 0.5370000004768372, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'BaseLevel': 1, 'SpellLevel': 1, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals an ally near your Penance target.', 'AuraDescription_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 6, 'SpellPriority': 50, 'SpellVisualID_1': 10981},
)
bonus_coefficients(penance_empowered_200160, direct=0.537,
    comment='Penance (Empowered) 200160 - same 0.537 direct coefficient as the normal Penance heal bolt 47750')


# --- (7,0) Greater Power Word: Shield ready marker -------------------------------------
greater_power_word_shield_ready_200161 = spell(
    id=200161,
    name='Greater Power Word: Shield',
    school=School.HOLY,
    duration_ms=30000,
    effects=[
        ApplyAura(AuraType.DUMMY, base_points=0, implicit_target_a=1),
    ],
    spell_icon_id=566,
    notes='Discipline rework (7,0): the "your next Power Word: Shield becomes Greater Power Word: '
          'Shield" marker the Renewed Hope capstone grants from a Penance bolt. Does not stack; '
          'spell_pri_power_word_shield consumes it AfterCast.',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your next Power Word: Shield also shields the 2 nearest injured allies.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next Power Word: Shield also shields the 2 nearest injured allies.', 'SpellClassSet': 6, 'SpellPriority': 50, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


# 200162 is deliberately left unused: it was reserved for a reduced Power Infusion for the
# Aspiration capstone, which the resolved design (PLAN §1) replaced with a plain re-cast of
# stock 10060 on the caster.


# --- (8,2) Grace rank 3 and the rank 1/2 buff clones -----------------------------------
grace_200163 = spell(
    id=200163,
    name='Grace',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=21, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=47930),
    ],
    spell_icon_id=2819,
    notes='Discipline rework (8,2) NEW rank 3 of Grace - 100% chance, triggering the stock 3%-per-'
          'stack buff 47930. Ranks 1-2 (47516/47517) keep their stock ids and trigger the 1%/2% '
          'clones 200164/200165 instead.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'CumulativeAura': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Flash Heal, Greater Heal, Penance and Power Word: Shield have a 100% chance to bless the target with Grace, increasing all healing received from you by 3%.  Stacks up to 3 times.  Lasts 12 sec.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': _GRACE_TRIGGER_MASK[0], 'EffectSpellClassMaskA_2': _GRACE_TRIGGER_MASK[1], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 16384, 'RangeIndex': 1, 'SpellClassSet': 6},
)
# Rank 3 is outside 47516's spell_ranks chain, so it needs its own positive spell_proc row
# (no duplicate-entry hazard - 200163 is a brand-new id nothing else covers).
procs_on(grace_200163, proc_flags=PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS, family_name=6,
         family_mask=_GRACE_TRIGGER_MASK, spell_phase_mask=PROC_SPELL_PHASE_HIT,
         attributes_mask=PROC_ATTR_TRIGGERED_CAN_PROC, chance=100)


# The 1%/2% Grace buffs - byte-for-byte clones of 47930 apart from the amount and the name-
# subtext. The EffectSpellClassMaskB_* dwords are copied verbatim and are load-bearing:
# SPELL_AURA_MOD_HEALING_RECEIVED (283) is filtered through AuraEffect::IsAffectedOnSpell in
# Unit::SpellHealingBonusTaken, so those bits are what restricts the bonus to the priest's
# own healing spells rather than to everything the target receives.
_GRACE_BUFF_RAW = {
    'AttributesEx3': 262272, 'AttributesEx5': 32, 'AttributesEx7': 268435456, 'CastingTimeIndex': 1,
    'ProcChance': 101, 'RangeIndex': 1, 'CumulativeAura': 3, 'EquippedItemClass': -1,
    'EffectDieSides_1': 1, 'EffectBasePoints_1': -1, 'EffectSpellClassMaskA_1': 64,
    'EffectSpellClassMaskB_1': 423894593, 'EffectSpellClassMaskB_2': 65572,
    'EffectSpellClassMaskB_3': 2147500036, 'Name_Lang_Mask': 16712190,
    'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190,
    'AuraDescription_Lang_enUS': 'Increases all healing received by the Priest by $s2%.',
    'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 6, 'SpellClassMask_2': 4096,
    'SpellClassMask_3': 1024, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0,
    'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_3': 1.0,
}

grace_buff_200164 = spell(
    id=200164,
    name='Grace',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    duration_ms=12000,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=21, apply_aura=AuraType.MOD_HEALING_RECEIVED),
    ],
    spell_icon_id=2819,
    notes='Discipline rework (8,2): Grace rank 1\'s 1%-per-stack buff, a clone of 47930.',
    raw_overrides=dict(_GRACE_BUFF_RAW, Description_Lang_enUS='Increases all healing received from the Priest by 1%.  Stacks up to 3 times.'),
)


grace_buff_200165 = spell(
    id=200165,
    name='Grace',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    duration_ms=12000,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=21, apply_aura=AuraType.MOD_HEALING_RECEIVED),
    ],
    spell_icon_id=2819,
    notes='Discipline rework (8,2): Grace rank 2\'s 2%-per-stack buff, a clone of 47930.',
    raw_overrides=dict(_GRACE_BUFF_RAW, Description_Lang_enUS='Increases all healing received from the Priest by 2%.  Stacks up to 3 times.'),
)


# --- (10,1) Spirit Shell absorb ---------------------------------------------------------
spirit_shell_absorb_200167 = spell(
    id=200167,
    name='Spirit Shell',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    range_yards=100.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, die_sides=0, implicit_target_a=21, apply_aura=AuraType.SCHOOL_ABSORB, misc_value=127),
    ],
    spell_icon_id=1804,
    notes='Discipline rework (10,1): the absorb shell Priest::TryConvertHealToSpiritShell puts on '
          'the target in place of a direct heal. Tracked separately from Divine Aegis (47753) and '
          'capped at 60% of the target\'s maximum health in C++. Attribute set copied from 47753; '
          'die_sides=0 because the amount always arrives as BP0 from CastCustomSpell. Icon shared '
          'with spirit_shell_200166 - see that spell\'s notes.',
    raw_overrides={'AttributesEx2': 2621440, 'AttributesEx3': 67108864, 'AttributesEx4': 1048576, 'CastingTimeIndex': 1, 'InterruptFlags': 8, 'ProcChance': 101, 'BaseLevel': 1, 'SpellLevel': 1, 'EquippedItemClass': -1, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Absorbs damage.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Absorbs damage.', 'SpellClassSet': 6, 'SpellClassMask_3': _masks.SPIRIT_SHELL, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


# ============================================================================================
# Priest Holy rework (docs/reworks/priest-holy-rework.md, .agents/plans/priest-rework/
# priest-rework.HOLY.md) - WP-0 prep. Rows below were bare stock data (npc.csv, now deleted from
# there) that the Holy pass needs to edit; pulled verbatim via
# `pull_dsl.py 33151 63731 63734 63735 63544 64128 33110 27827 --constants` (PLAN sec 3.4 - editing
# an undeclared ID is a silent no-op) and pasted unmodified here. WP-A edits these in place for its
# own talents; this pass leaves them as pulled.
# ============================================================================================

surge_of_light_33151 = spell(
    id=33151,
    name='Surge of Light',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=10),
        Effect(type=EffectType.APPLY_AURA, base_points=59, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=2176,
    notes='Priest Holy rework (HOLY.md 5,0): design doc §5.7 - "the free cast can now crit and '
          're-roll this proc" - so the old eff3 (crit-block, misc=7/SPELLMOD_CRITICAL_CHANCE '
          '-100%) is REPURPOSED (only 3 effect slots exist) into SPELLMOD_DAMAGE +60% '
          '(base_points=59) scoped to Smite only (EffectSpellClassMaskC_1 below), matching '
          'PLAN §2\'s "applied unconditionally" (no PvP-only clause) call. StackAmount=2, '
          'ProcCharges=0 (stack consumption handled in C++ by spell_pri_surge_of_light_consume, '
          'not the native charge system, so a second stack survives a partial consume).',
    raw_overrides={'ShapeshiftExclude': 1073741824, 'CastingTimeIndex': 1, 'ProcTypeMask': 81920, 'ProcChance': 100, 'ProcCharges': 0, 'StackAmount': 2, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 2176, 'EffectSpellClassMaskB_1': 2176, 'EffectSpellClassMaskC_1': _masks.SMITE, 'SpellVisualID_1': 12989, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your next Smite or Flash Heal spell is instant cast and costs no mana. If it is Smite, its damage is increased by 60%.  This effect lasts $33151d, stacking up to 2 times.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next Smite or Flash Heal spell is instant cast and costs no mana.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 6, 'SpellClassMask_2': 4096, 'SpellClassMask_3': 1024, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


serendipity_63731 = spell(
    id=63731,
    name='Serendipity',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-6, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.CASTING_TIME),
        Effect(type=EffectType.APPLY_AURA, base_points=-6, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COST),
    ],
    spell_icon_id=2900,
    notes='Priest Holy rework (HOLY.md 7,2): this is the rank-1 (63730) buff (confirmed via the live '
          'trigger_spell wiring on the talent ranks below, NOT ascending spell-ID order - see the '
          "note on 63734/63735 for why HOLY.md's own listing order doesn't match). -5% (base_points "
          '-6, hand-authored convention now that this row is edited rather than left pulled) on both '
          'cast time and a new SPELLMOD_COST effect. Mask corrected to Greater Heal|Prayer of '
          'Healing (4608) - the pulled stock value (6144 = Greater Heal|Flash Heal) did not actually '
          'match either this row\'s own tooltip text or HOLY.md\'s target mask.',
    raw_overrides={'CastingTimeIndex': 1, 'ProcTypeMask': 17408, 'ProcChance': 100, 'ProcCharges': 1, 'RangeIndex': 1, 'CumulativeAura': 3, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 4608, 'EffectSpellClassMaskB_1': 4608, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'NameSubtext_Lang_enUS': '', 'Description_Lang_enUS': 'When you heal with Binding Heal or Flash Heal, casting Renew, or damaging with Smite, the cast time and mana cost of your next Greater Heal or Prayer of Healing spell is reduced by $63731s1%. Stacks up to 3 times. Lasts $63731d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Reduces the cast time and mana cost of your next Greater Heal or Prayer of Healing by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 6, 'SpellClassMask_2': 4096, 'SpellClassMask_3': 1024, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


serendipity_63734 = spell(
    id=63734,
    name='Serendipity',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-16, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.CASTING_TIME),
        Effect(type=EffectType.APPLY_AURA, base_points=-16, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COST),
    ],
    spell_icon_id=2900,
    notes='Priest Holy rework (HOLY.md 7,2): this is the rank-3 (63737) buff, per the live '
          'trigger_spell wiring (serendipity_63737.trigger_spell == 63734) - HOLY.md\'s own listing '
          'reads 63731/63734/63735 in ascending ID order and assumes that is rank order, but the '
          "live data does not wire the ranks to their buffs in ascending-ID order (rank 2's own "
          'talent, 63733, triggers 63735, not 63734) - flagged as HOLY.md getting the ID-to-rank '
          'mapping wrong; values below follow the ACTUAL wiring (rank -> its own trigger_spell), not '
          "HOLY.md's listing order. -15% (base_points -16) on both cast time and a new SPELLMOD_COST "
          'effect. Mask corrected to Greater Heal|Prayer of Healing (4608), same fix as 63731.',
    raw_overrides={'CastingTimeIndex': 1, 'ProcTypeMask': 17408, 'ProcChance': 100, 'ProcCharges': 1, 'RangeIndex': 1, 'CumulativeAura': 3, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 4608, 'EffectSpellClassMaskB_1': 4608, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'NameSubtext_Lang_enUS': '', 'Description_Lang_enUS': 'When you heal with Binding Heal or Flash Heal, casting Renew, or damaging with Smite, the cast time and mana cost of your next Greater Heal or Prayer of Healing spell is reduced by $63734s1%. Stacks up to 3 times. Lasts $63734d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Reduces the cast time and mana cost of your next Greater Heal or Prayer of Healing by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 6, 'SpellClassMask_2': 4096, 'SpellClassMask_3': 1024, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


serendipity_63735 = spell(
    id=63735,
    name='Serendipity',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.CASTING_TIME),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COST),
    ],
    spell_icon_id=2900,
    notes='Priest Holy rework (HOLY.md 7,2): this is the rank-2 (63733) buff, per the live '
          'trigger_spell wiring (serendipity_63733.trigger_spell == 63735) - see 63734\'s own notes '
          'for the ID-order mismatch this uncovered. -10% (base_points -11) on both cast time and a '
          'new SPELLMOD_COST effect. Mask corrected to Greater Heal|Prayer of Healing (4608).',
    raw_overrides={'CastingTimeIndex': 1, 'ProcTypeMask': 17408, 'ProcChance': 100, 'ProcCharges': 1, 'RangeIndex': 1, 'CumulativeAura': 3, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 4608, 'EffectSpellClassMaskB_1': 4608, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'NameSubtext_Lang_enUS': '', 'Description_Lang_enUS': 'When you heal with Binding Heal or Flash Heal, casting Renew, or damaging with Smite, the cast time and mana cost of your next Greater Heal or Prayer of Healing spell is reduced by $63735s1%. Stacks up to 3 times. Lasts $63735d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Reduces the cast time and mana cost of your next Greater Heal or Prayer of Healing by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 6, 'SpellClassMask_2': 4096, 'SpellClassMask_3': 1024, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


empowered_renew_63544 = spell(
    id=63544,
    name='Empowered Renew',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.HEAL, base_points=-1, implicit_target_a=21),
    ],
    spell_icon_id=3021,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx3': 1073741824, 'ShapeshiftMask': 2147483648, 'ShapeshiftExclude': 134217728, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 1, 'SpellLevel': 1, 'EquippedItemClass': -1, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Your Renew spell gains an additional portion of your bonus healing effects, and your Renew will instantly heal the target for a portion of the total periodic effect.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 6, 'SpellClassMask_3': 4096, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


body_and_soul_64128 = spell(
    id=64128,
    name='Body and Soul',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=3000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=21, apply_aura=AuraType.MOD_INCREASE_SPEED),
    ],
    spell_icon_id=3106,
    notes='HOLY.md 7,0: rank 1 speed buff (30%, base_points=29 unchanged). duration_ms 4000 -> 3000 '
          '(design doc row 7,0 / HOLY.md "64128 speed 30/60, 3 s"; talent-tooltip-audit fix, WP-C). '
          'Description rewritten for the Renew/Leap of Faith retarget (was stale Power Word: Shield/ '
          'Abolish Disease text).',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'EquippedItemClass': -1, 'EffectDieSides_2': 1, 'EffectDieSides_3': 1, 'EffectBasePoints_2': -1, 'EffectBasePoints_3': -1, 'EffectSpellClassMaskA_1': 402653696, 'EffectSpellClassMaskA_2': 4, 'EffectSpellClassMaskB_3': 4, 'EffectSpellClassMaskC_2': 32, 'SpellVisualID_1': 13827, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': "Casting Renew or Leap of Faith increases the target's movement speed by $s1% for $d.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement speed increased by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 6, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0},
)


body_and_soul_65081 = spell(
    id=65081,
    name='Body and Soul',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=3000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=59, implicit_target_a=21, apply_aura=AuraType.MOD_INCREASE_SPEED),
    ],
    spell_icon_id=3106,
    notes="HOLY.md 7,0: rank 2's own speed buff (60%, base_points=59) - never pulled into the DSL "
          "before now (talent-tooltip-audit fix, WP-C: body_and_soul_64129's own PROC_TRIGGER_SPELL "
          "points at this id, but it was undeclared, so 64129's tooltip borrowed 64128's $d token "
          "instead of its own). duration_ms 4000 -> 3000 and description rewritten to match 64128's "
          "same fix (both ranks share the same 3 sec duration and Renew/Leap of Faith retarget).",
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'EquippedItemClass': -1, 'EffectDieSides_2': 1, 'EffectDieSides_3': 1, 'EffectBasePoints_2': -1, 'EffectBasePoints_3': -1, 'EffectSpellClassMaskA_1': 402653696, 'EffectSpellClassMaskA_2': 4, 'EffectSpellClassMaskB_3': 4, 'EffectSpellClassMaskC_2': 32, 'SpellVisualID_1': 13827, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': "Casting Renew or Leap of Faith increases the target's movement speed by $s1% for $d.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement speed increased by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 6, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0},
)


prayer_of_mending_33110 = spell(
    id=33110,
    name='Prayer of Mending',
    school=School.HOLY,
    attributes=134479872,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.HEAL, implicit_target_a=1),
    ],
    spell_icon_id=2219,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx2': 4, 'AttributesEx3': 1073741824, 'TargetCreatureType': 767, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 1, 'SpellLevel': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 1714, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Places a spell on the target that heals them the next time they take damage.  When the heal occurs, Prayer of Mending jumps to a party or raid member within $41635a1 yards. Jumps up to $48113n times and lasts $48111d after each jump. This spell can only be placed on one target at a time.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 6, 'SpellClassMask_2': 32, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


# spirit_of_redemption_27827 is the stock on-death "FORM_SPIRITOFREDEMPTION" spell
# Unit::Kill(Unit.cpp:13787-13830)'s hardcode currently casts when it finds 20711's DUMMY - that
# whole block is deleted by this pass (PLAN sec 6.8, HOLY.md "Core hardcode migration owed by this
# pass"), so 27827 goes unreferenced once WP-B lands. Declared anyway per PLAN sec 3.4 (an
# undeclared id can't be edited later without being a silent no-op) and left otherwise untouched.
spirit_of_redemption_27827 = spell(
    id=27827,
    name='Spirit of Redemption',
    school=School.HOLY,
    attributes=8454144,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.HEAL, implicit_target_a=1),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=82),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=36, misc_value=32),
    ],
    spell_icon_id=241,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 1, 'AttributesEx3': 1048576, 'ShapeshiftExclude': 134217728, 'CastingTimeIndex': 1, 'AuraInterruptFlags': 527360, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'Increases total Spirit by $20711s2% and upon death, the priest becomes the Spirit of Redemption for $27827d.  The Spirit of Redemption cannot move, attack, be attacked or targeted by any spells or effects.  While in this form the priest can cast any healing spell free of cost.  When the effect ends, the priest dies.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'You have become more powerful than anyone can possibly imagine.', 'AuraDescription_Lang_Mask': 16712190, 'StartRecoveryCategory': 133, 'SpellClassSet': 6, 'SpellClassMask_3': 512, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


# =====================================================================================
# Priest Holy rework (docs/reworks/priest-holy-rework.md,
# .agents/plans/priest-rework/priest-rework.HOLY.md) - all brand-new hidden trigger/buff spells
# and new talent-rank spells (200172-200226, per HOLY.md's "ID map"). Player-castable new spells
# (Holy Word: Serenity/Sanctify/Chastise, Apotheosis) live in priest_spells.py instead - see that
# file's own "Priest Holy rework" section.
# =====================================================================================

# --- 0,0 Healing Focus capstone -------------------------------------------------------
healing_focus_capstone_200172 = spell(
    id=200172,
    name='Healing Focus',
    school=School.HOLY,
    cast_time_ms=0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL),
    ],
    spell_icon_id=1871,
    notes='HOLY.md 0,0: Healing Focus capstone buff. +2% generalized haste (base_points=1), '
          'StackAmount=3, 10 s. spell_pri_healing_focus_capstone (AuraScript on 15012) casts this '
          'on self, stacking, after a Greater Heal/Prayer of Healing/Divine Hymn cast completes.',
    raw_overrides={'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell haste by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Spell haste increased by $s1%.', 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'StackAmount': 3, 'SpellVisualID_1': 1155, 'EffectChainAmplitude_1': 1.0},
)


# --- 1,0 Divine Touch (NEW talent 60011) -----------------------------------------------
divine_touch_200174 = spell(
    id=200174,
    name='Divine Touch',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200176),
    ],
    spell_icon_id=237,
    notes='HOLY.md 1,0/design doc §5.6: rank 1, 2% chance (procs_on below) on Renew periodic '
          "healing only (Empowered Renew's instant chunk and Blessed Recovery's payout are "
          'non-periodic and cannot roll it, by construction of the proc flag). 5 s per-caster '
          'lockout is the spell_proc row\'s own Cooldown, not a spell cooldown (design doc §1: no '
          'Cooldown Haste on internal cooldowns).',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your Renew's periodic healing has a 2% chance to grant Divine Touch: your next Greater Heal is instant and free. Lasts 15 sec. Once per 5 sec.", 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your Renew has a chance to grant Divine Touch.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectChainAmplitude_1': 1.0},
)
procs_on(divine_touch_200174, PROC_FLAG_DONE_PERIODIC, family_name=6, family_mask=(_masks.RENEW, 0, 0),
         spell_type_mask=PROC_SPELL_TYPE_HEAL, chance=2, cooldown_ms=5000)


divine_touch_200175 = spell(
    id=200175,
    name='Divine Touch',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200176),
    ],
    spell_icon_id=237,
    notes='HOLY.md 1,0: rank 2, 4% chance.',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your Renew's periodic healing has a 4% chance to grant Divine Touch: your next Greater Heal is instant and free. Lasts 15 sec. Once per 5 sec.", 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your Renew has a chance to grant Divine Touch.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectChainAmplitude_1': 1.0},
)
procs_on(divine_touch_200175, PROC_FLAG_DONE_PERIODIC, family_name=6, family_mask=(_masks.RENEW, 0, 0),
         spell_type_mask=PROC_SPELL_TYPE_HEAL, chance=4, cooldown_ms=5000)


divine_touch_buff_200176 = spell(
    id=200176,
    name='Divine Touch',
    school=School.HOLY,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.CASTING_TIME),
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COST),
    ],
    spell_icon_id=237,
    notes='HOLY.md 1,0: the Divine Touch buff - next Greater Heal instant (-100% cast time) and free '
          '(-100% cost), scoped to Greater Heal only (both effects), 1 charge, 15 s, no stack.',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your next Greater Heal is instant and free.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next Greater Heal is instant and free.', 'EquippedItemClass': -1, 'ProcChance': 101, 'ProcCharges': 1, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': _masks.GREATER_HEAL, 'EffectSpellClassMaskB_1': _masks.GREATER_HEAL, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0},
)


# --- 1,1 Blessed Recovery capstone payout ----------------------------------------------
blessed_recovery_heal_200177 = spell(
    id=200177,
    name='Blessed Recovery',
    school=School.HOLY,
    cast_time_ms=0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=0, implicit_target_a=1),
    ],
    spell_icon_id=1875,
    notes='HOLY.md 1,1/design doc §5.5: the capstone instant-heal payout - script-set BasePoints via '
          'CastCustomSpell (2 Renew ticks worth), crit rolls normally.',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals the target.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectChainAmplitude_1': 1.0},
)


blessed_recovery_lockout_200178 = spell(
    id=200178,
    name='Blessed Recovery',
    school=School.HOLY,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1875,
    notes='HOLY.md 1,1: hidden 20 s per-target-per-caster lockout marker (design doc §5.5) - not a '
          'spell cooldown, so no Cooldown Haste.',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Blessed Recovery cannot trigger again on this target yet.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Blessed Recovery is on cooldown for this target.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'AttributesEx': 1024, 'EffectChainAmplitude_1': 1.0},
)


# --- 2,1 Answered Prayers (NEW talent 60012) --------------------------------------------
answered_prayers_200179 = spell(
    id=200179,
    name='Answered Prayers',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200182),
    ],
    spell_icon_id=2819,
    notes='HOLY.md 2,1/design doc §5.4: rank 1, 5% chance (procs_on below) on a Greater Heal cast.',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Greater Heal cast has a 5% chance to restore 2% of your maximum mana and cause your next Renew to also apply to 2 additional allies within 30 yds. Lasts 15 sec, no stack.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your Greater Heal has a chance to grant Answered Prayers.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectChainAmplitude_1': 1.0},
)
procs_on(answered_prayers_200179, PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS, spell_phase_mask=PROC_SPELL_PHASE_CAST,
         family_name=6, family_mask=(_masks.GREATER_HEAL, 0, 0), chance=5)


answered_prayers_200180 = spell(
    id=200180,
    name='Answered Prayers',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200182),
    ],
    spell_icon_id=2819,
    notes='HOLY.md 2,1: rank 2, 10% chance.',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Greater Heal cast has a 10% chance to restore 2% of your maximum mana and cause your next Renew to also apply to 2 additional allies within 30 yds. Lasts 15 sec, no stack.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your Greater Heal has a chance to grant Answered Prayers.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectChainAmplitude_1': 1.0},
)
procs_on(answered_prayers_200180, PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS, spell_phase_mask=PROC_SPELL_PHASE_CAST,
         family_name=6, family_mask=(_masks.GREATER_HEAL, 0, 0), chance=10)


answered_prayers_200181 = spell(
    id=200181,
    name='Answered Prayers',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200182),
    ],
    spell_icon_id=2819,
    notes='HOLY.md 2,1: rank 3, 15% chance.',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Greater Heal cast has a 15% chance to restore 2% of your maximum mana and cause your next Renew to also apply to 2 additional allies within 30 yds. Lasts 15 sec, no stack.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your Greater Heal has a chance to grant Answered Prayers.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectChainAmplitude_1': 1.0},
)
procs_on(answered_prayers_200181, PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS, spell_phase_mask=PROC_SPELL_PHASE_CAST,
         family_name=6, family_mask=(_masks.GREATER_HEAL, 0, 0), chance=15)


answered_prayers_buff_200182 = spell(
    id=200182,
    name='Answered Prayers',
    school=School.HOLY,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.ENERGIZE_PCT, base_points=2, implicit_target_a=1),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2819,
    notes='HOLY.md 2,1: the Answered Prayers buff - eff1 ENERGIZE_PCT (137, a direct SPELL_EFFECT, '
          'not an APPLY_AURA) restores 2% mana immediately on application; eff2 is the hidden '
          'DUMMY marker spell_pri_renew_cast reads (HasAura check) to know the next Renew cast '
          'should spread. 15 s, no stack.',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your next Renew also applies to 2 additional allies within 30 yds.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next Renew also applies to 2 additional allies within 30 yds.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0},
)


# --- 2,2 Improved Holy Nova (NEW talent 60013) ------------------------------------------
improved_holy_nova_200183 = spell(
    id=200183,
    name='Improved Holy Nova',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=1874,
    notes='HOLY.md 2,2: rank 1, +10% (base_points=9), scoped to BOTH Holy Nova bits - damage '
          '(15237) and heal (23455) - EffectSpellClassMaskA_1 below, since HOLY.md flags they use '
          'different family bits and both need covering on this one effect slot.',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage and healing of your Holy Nova spell by $s1%.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': _masks.HOLY_NOVA_DMG | _masks.HOLY_NOVA_HEAL, 'EffectChainAmplitude_1': 1.0},
)


improved_holy_nova_200184 = spell(
    id=200184,
    name='Improved Holy Nova',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=1874,
    notes='HOLY.md 2,2: rank 2, +20% (base_points=19).',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage and healing of your Holy Nova spell by $s1%.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': _masks.HOLY_NOVA_DMG | _masks.HOLY_NOVA_HEAL, 'EffectChainAmplitude_1': 1.0},
)


# --- 3,0 Holy Reach capstone mana restore -----------------------------------------------
holy_reach_mana_200185 = spell(
    id=200185,
    name='Holy Reach',
    school=School.HOLY,
    duration_ms=4000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.PERIODIC_ENERGIZE, amplitude=1000),
    ],
    spell_icon_id=300,
    notes='HOLY.md 3,0/design doc §5.7: capstone mana-restore-over-time - BasePoints set by script '
          '(CastCustomSpell, missing mana x 2% / 4 ticks), PERIODIC_ENERGIZE over 4 sec.',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Restores mana over 4 sec.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Restoring mana.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectChainAmplitude_1': 1.0},
)


# --- 3,2 Searing Light rank 3 ------------------------------------------------------------
searing_light_200186 = spell(
    id=200186,
    name='Searing Light',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=-26, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COST),
    ],
    spell_icon_id=1868,
    notes='HOLY.md 3,2: rank 3 (14909/15017 are ranks 1/2, unchanged trims). Mirrors ranks 1/2\'s own '
          'two-effect shape exactly (eff1 misc=0 + eff2 misc=22, both damage +15%/base_points=14) '
          'rather than collapsing to one, since some of the covered spells (Holy Fire\'s DoT '
          'portion) read the misc=22 variant - same masks as 14909/15017 (Smite|HF|Holy Nova dmg|'
          'Penance dmg bolt on eff1, Holy Fire only on eff2). New eff3 SPELLMOD_COST -25% '
          '(base_points=-26) scoped Holy Nova damage only.',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Smite, Holy Fire, Holy Nova and Penance spells by $s1%, and reduces the mana cost of your Holy Nova by $s2%.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': 5243008, 'EffectSpellClassMaskA_2': 32768, 'EffectSpellClassMaskA_3': _masks.PENANCE_BOLT, 'EffectSpellClassMaskB_1': 1048576, 'EffectSpellClassMaskC_1': _masks.HOLY_NOVA_DMG, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


# --- 3,3 Kindled Faith (NEW talent 60014) -----------------------------------------------
kindled_faith_200187 = spell(
    id=200187,
    name='Kindled Faith',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=156,
    notes='HOLY.md 3,3: rank 1, 8% chance (procs_on below) on Smite damage. Icon reuses Holy '
          "Fire's own (156, talent-tooltip-audit fix, WP-C: originally 1868, an unintentional "
          'collision with Searing Light).',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Smite has an 8% chance to reset the cooldown of Holy Fire and make your next Holy Fire instant. Lasts 10 sec, no stack.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectChainAmplitude_1': 1.0},
)
procs_on(kindled_faith_200187, PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG, family_name=6,
         family_mask=(_masks.SMITE, 0, 0), chance=8)
scripted_by(kindled_faith_200187, 'spell_pri_kindled_faith')


kindled_faith_200188 = spell(
    id=200188,
    name='Kindled Faith',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=156,
    notes='HOLY.md 3,3: rank 2, 16% chance. Icon reuses Holy Fire\'s own (156, talent-tooltip-audit '
          'fix, WP-C).',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Smite has a 16% chance to reset the cooldown of Holy Fire and make your next Holy Fire instant. Lasts 10 sec, no stack.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectChainAmplitude_1': 1.0},
)
procs_on(kindled_faith_200188, PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG, family_name=6,
         family_mask=(_masks.SMITE, 0, 0), chance=16)
scripted_by(kindled_faith_200188, 'spell_pri_kindled_faith')


kindled_faith_200189 = spell(
    id=200189,
    name='Kindled Faith',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=156,
    notes='HOLY.md 3,3: rank 3, 25% chance. Icon reuses Holy Fire\'s own (156, talent-tooltip-audit '
          'fix, WP-C).',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Smite has a 25% chance to reset the cooldown of Holy Fire and make your next Holy Fire instant. Lasts 10 sec, no stack.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectChainAmplitude_1': 1.0},
)
procs_on(kindled_faith_200189, PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG, family_name=6,
         family_mask=(_masks.SMITE, 0, 0), chance=25)
scripted_by(kindled_faith_200189, 'spell_pri_kindled_faith')


kindled_faith_buff_200190 = spell(
    id=200190,
    name='Kindled Faith',
    school=School.HOLY,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.CASTING_TIME),
    ],
    spell_icon_id=156,
    notes='HOLY.md 3,3: the Kindled Faith buff - next Holy Fire instant (-100% cast time), scoped to '
          "Holy Fire only, 1 charge, 10 s, no stack. Icon reuses Holy Fire's own (156, "
          'talent-tooltip-audit fix, WP-C).',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your next Holy Fire is instant.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next Holy Fire is instant.', 'EquippedItemClass': -1, 'ProcChance': 101, 'ProcCharges': 1, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': _masks.HOLY_FIRE, 'EffectChainAmplitude_1': 1.0},
)


# --- 4,1 Spirit of Redemption capstone (ranks 2/3, marker, form, free heals) ------------
spirit_of_redemption_200191 = spell(
    id=200191,
    name='Spirit of Redemption',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=137, misc_value=4),
    ],
    spell_icon_id=1654,
    notes='HOLY.md 4,1: rank 2, Spirit +6% (base_points=5). No DUMMY - the on-death hardcode this '
          "talent used to key off is deleted by this pass (see 20711's own notes). Capstone "
          'preview text added per PLAN sec 3.1 (talent-tooltip-audit fix, WP-C).',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases total Spirit by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Absorb otherwise lethal damage up to 300% of Spirit. If it prevents death, become a Spirit of Redemption for 5 sec: cannot move or attack, 50% reduced damage taken, Holy Priest heals cost no mana. Shares a 2 min cooldown with Ardent Defender and Cheat Death.|r', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectChainAmplitude_1': 1.0},
)


spirit_of_redemption_200192 = spell(
    id=200192,
    name='Spirit of Redemption',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=137, misc_value=4),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.SCHOOL_ABSORB, misc_value=127),
    ],
    spell_icon_id=1654,
    notes='HOLY.md 4,1: rank 3 (final kept rank), Spirit +9% (base_points=8) plus the capstone '
          'absorb (eff2 SCHOOL_ABSORB, misc 127 = all schools, base_points=-1/script-driven - '
          'spell_pri_spirit_of_redemption computes the actual absorb amount as '
          'min(damage, 3xSpirit) on OnEffectAbsorb and, if it prevents death and no 200193 is up, '
          'casts 200193+200194+200226 on self). Tooltip capstone line, final rank plain color.',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases total Spirit by $s1%.\n\nCapstone Bonus: Absorb otherwise lethal damage up to 300% of Spirit. If it prevents death, become a Spirit of Redemption for 5 sec: cannot move or attack, 50% reduced damage taken, Holy Priest heals cost no mana. Shares a 2 min cooldown with Ardent Defender and Cheat Death.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0},
)
scripted_by(spirit_of_redemption_200192, 'spell_pri_spirit_of_redemption')


cheated_death_200193 = spell(
    id=200193,
    name='Cheated Death',
    school=School.NORMAL,
    duration_ms=120000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1654,
    notes='PLAN §1/§4.4: shared 2-min marker between Spirit of Redemption, Cheat Death (Rogue) and '
          'Ardent Defender (Paladin) - HasAura(200193) on any of the three blocks the others. '
          'Hidden, no visible aura icon needed but not attribute-hidden either (PLAN gives no '
          "explicit hide instruction and Discipline's own shared markers stay visible - kept "
          'consistent).',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You cannot be saved from death by Spirit of Redemption, Cheat Death or Ardent Defender.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Cannot be saved from death again.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectChainAmplitude_1': 1.0},
)


spirit_of_redemption_form_200194 = spell(
    id=200194,
    name='Spirit of Redemption',
    school=School.HOLY,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MOD_PACIFY),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MOD_ROOT),
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
    ],
    spell_icon_id=1654,
    notes='HOLY.md 4,1: the on-death form - pacify + root + -50% damage taken (base_points=-51), 5 s.',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You have become a Spirit of Redemption. You cannot move or attack, and take 50% reduced damage.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Spirit of Redemption.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


spirit_of_redemption_free_heals_200226 = spell(
    id=200226,
    name='Spirit of Redemption',
    school=School.HOLY,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COST),
    ],
    spell_icon_id=1654,
    notes='HOLY.md 4,1 ID map: "4th effect of the form" - a separate spell (not a 4th Effect slot, '
          'which does not exist) cast alongside 200193/200194 by spell_pri_spirit_of_redemption. '
          '-100% cost (base_points=-101) scoped to PRIEST_HEAL_MASK on all three dwords, 5 s.',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Holy Priest heals cost no mana.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Heals cost no mana.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': _masks.PRIEST_HEAL_MASK[0], 'EffectSpellClassMaskA_2': _masks.PRIEST_HEAL_MASK[1], 'EffectSpellClassMaskA_3': _masks.PRIEST_HEAL_MASK[2], 'EffectChainAmplitude_1': 1.0},
)


# --- 4,3 Improved Prayer of Mending (NEW talent 60015) ----------------------------------
improved_prayer_of_mending_200195 = spell(
    id=200195,
    name='Improved Prayer of Mending',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=-2000, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COOLDOWN),
    ],
    spell_icon_id=2219,
    notes='HOLY.md 4,3: rank 1, healing +10% (base_points=9) and cooldown -2000 ms, both scoped to '
          "Prayer of Mending's dw2 bit 32 (also covers the 33110 heal jump, same bit).",
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the healing of your Prayer of Mending by $s1%, and reduces its cooldown by $/1000;s2 sec.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectSpellClassMaskA_2': _masks.POM, 'EffectSpellClassMaskB_2': _masks.POM, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0},
)


improved_prayer_of_mending_200196 = spell(
    id=200196,
    name='Improved Prayer of Mending',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=-4000, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COOLDOWN),
    ],
    spell_icon_id=2219,
    notes='HOLY.md 4,3: rank 2, healing +20% (base_points=19), cooldown -4000 ms.',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the healing of your Prayer of Mending by $s1%, and reduces its cooldown by $/1000;s2 sec.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectSpellClassMaskA_2': _masks.POM, 'EffectSpellClassMaskB_2': _masks.POM, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0},
)


# --- 6,0 Holy Concentration Spirit buffs -------------------------------------------------
holy_concentration_buff_200199 = spell(
    id=200199,
    name='Holy Concentration',
    school=School.HOLY,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=137, misc_value=4),
    ],
    spell_icon_id=2169,
    notes='HOLY.md 6,0: rank 1 buff, Spirit +10% (base_points=9), 12 s.',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases total Spirit by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Spirit increased by $s1%.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectChainAmplitude_1': 1.0},
)


holy_concentration_buff_200200 = spell(
    id=200200,
    name='Holy Concentration',
    school=School.HOLY,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=137, misc_value=4),
    ],
    spell_icon_id=2169,
    notes='HOLY.md 6,0: rank 2 buff, Spirit +20% (base_points=19).',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases total Spirit by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Spirit increased by $s1%.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectChainAmplitude_1': 1.0},
)


holy_concentration_buff_200201 = spell(
    id=200201,
    name='Holy Concentration',
    school=School.HOLY,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=137, misc_value=4),
    ],
    spell_icon_id=2169,
    notes='HOLY.md 6,0: rank 3 buff, Spirit +30% (base_points=29).',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases total Spirit by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Spirit increased by $s1%.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectChainAmplitude_1': 1.0},
)


# --- 6,1 Lightwell auto-heal --------------------------------------------------------------
lightwell_heal_200202 = spell(
    id=200202,
    name='Lightwell',
    school=School.HOLY,
    cast_time_ms=0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=289, die_sides=1, implicit_target_a=1),
    ],
    spell_icon_id=1878,
    notes='HOLY.md 6,1/baseline edits: the Lightwell object\'s own auto-heal, cast by '
          'npc_pet_pri_lightwell (WP-B, pet_priest.cpp) once per sec at the party/raid member most '
          'in need within 20 yds. 290 (base_points=289) + 0.4 SP (bonus_coefficients below) - PLAN '
          "§2's default (spec text gives no coefficient).",
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals the target for $s1.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectChainAmplitude_1': 1.0},
)
bonus_coefficients(lightwell_heal_200202, direct=0.4)


# --- 6,2 Blessed Warding (REPURPOSED talent 411, was Spell Warding) ---------------------
blessed_warding_200203 = spell(
    id=200203,
    name='Blessed Warding',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1880,
    notes='HOLY.md 6,2: rank 1 - eff1 spell damage taken -2% (base_points=-3, misc 126 = magic '
          "schools). eff2 hidden marker holding the healing-done-%-per-stack tuning (1%), read by "
          'spell_pri_blessed_warding to size the 200206 buff cast.',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces spell damage taken by $s1%. Taking area or periodic damage increases your healing done by $s2% for 10 sec, stacking up to 3 times.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0},
)
procs_on(blessed_warding_200203, PROC_FLAG_TAKEN_SPELL_MAGIC_DMG_CLASS_NEG | PROC_FLAG_TAKEN_PERIODIC, chance=100)
scripted_by(blessed_warding_200203, 'spell_pri_blessed_warding')


blessed_warding_200204 = spell(
    id=200204,
    name='Blessed Warding',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1880,
    notes='HOLY.md 6,2: rank 2 - damage taken -4% (base_points=-5); healing-done marker 2% (base_points=1).',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces spell damage taken by $s1%. Taking area or periodic damage increases your healing done by $s2% for 10 sec, stacking up to 3 times.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0},
)
procs_on(blessed_warding_200204, PROC_FLAG_TAKEN_SPELL_MAGIC_DMG_CLASS_NEG | PROC_FLAG_TAKEN_PERIODIC, chance=100)
scripted_by(blessed_warding_200204, 'spell_pri_blessed_warding')


blessed_warding_200205 = spell(
    id=200205,
    name='Blessed Warding',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-7, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1880,
    notes='HOLY.md 6,2: rank 3 - damage taken -6% (base_points=-7); healing-done marker 3% (base_points=2).',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces spell damage taken by $s1%. Taking area or periodic damage increases your healing done by $s2% for 10 sec, stacking up to 3 times.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0},
)
procs_on(blessed_warding_200205, PROC_FLAG_TAKEN_SPELL_MAGIC_DMG_CLASS_NEG | PROC_FLAG_TAKEN_PERIODIC, chance=100)
scripted_by(blessed_warding_200205, 'spell_pri_blessed_warding')


blessed_warding_buff_200206 = spell(
    id=200206,
    name='Blessed Warding',
    school=School.HOLY,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.MOD_HEALING_DONE_PERCENT),
    ],
    spell_icon_id=1880,
    notes='HOLY.md 6,2: the Blessed Warding buff - healing done % (BasePoints set by script per rank, '
          'CastCustomSpell), StackAmount=3, 10 s.',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases healing done by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Healing done increased by $s1%.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'StackAmount': 3, 'EffectChainAmplitude_1': 1.0},
)


# --- 6,3 Radiant Fury (REPURPOSED talent 1765, was Blessed Resilience) -------------------
radiant_fury_200207 = spell(
    id=200207,
    name='Radiant Fury',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.BONUS_MULTIPLIER),
        Effect(type=EffectType.APPLY_AREA_AURA_RAID, base_points=0, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL, radius_yards=50.0),
    ],
    spell_icon_id=2177,
    notes='HOLY.md 6,3: rank 1 - eff1 SPELLMOD_BONUS_MULTIPLIER (24, the same aura/op Empowered '
          'Healing uses for "additional % of bonus") +7% (base_points=6) scoped Smite|HF|Holy Nova '
          'dmg. eff2 APPLY_AREA_AURA_RAID (65, precedent: Improved Icy Talons 55610) generalized '
          'haste (193) +1% (base_points=0) to raid within 50 yds.',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the bonus spell damage of your Smite, Holy Fire and Holy Nova by $s1%, and increases the spell haste of party and raid members within 50 yds by $s2%.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': _masks.SMITE | _masks.HOLY_FIRE | _masks.HOLY_NOVA_DMG, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0},
)


radiant_fury_200208 = spell(
    id=200208,
    name='Radiant Fury',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=13, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.BONUS_MULTIPLIER),
        Effect(type=EffectType.APPLY_AREA_AURA_RAID, base_points=1, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL, radius_yards=50.0),
    ],
    spell_icon_id=2177,
    notes='HOLY.md 6,3: rank 2, +14% (base_points=13) / +2% raid haste (base_points=1).',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the bonus spell damage of your Smite, Holy Fire and Holy Nova by $s1%, and increases the spell haste of party and raid members within 50 yds by $s2%.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': _masks.SMITE | _masks.HOLY_FIRE | _masks.HOLY_NOVA_DMG, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0},
)
radiant_fury_200209 = spell(
    id=200209,
    name='Radiant Fury',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.BONUS_MULTIPLIER),
        Effect(type=EffectType.APPLY_AREA_AURA_RAID, base_points=2, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL, radius_yards=50.0),
    ],
    spell_icon_id=2177,
    notes='HOLY.md 6,3: rank 3, +20% (base_points=19) / +3% raid haste (base_points=2). PLAN §8 '
          'accepted risk #5 - this may collide with Improved Moonkin Form.',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the bonus spell damage of your Smite, Holy Fire and Holy Nova by $s1%, and increases the spell haste of party and raid members within 50 yds by $s2%.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': _masks.SMITE | _masks.HOLY_FIRE | _masks.HOLY_NOVA_DMG, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0},
)
# --- end Radiant Fury ---


# --- 7,3 Holy Wrath (NEW talent 60018) ---------------------------------------------------
_HOLY_WRATH_DMG_MASK = (_masks.SMITE | _masks.HOLY_FIRE | _masks.HOLY_NOVA_DMG,
                        0,
                        _masks.PENANCE_BOLT | _masks.HW_CHASTISE | _masks.HALO | _masks.DIVINE_STAR)

holy_wrath_200210 = spell(
    id=200210,
    name='Holy Wrath',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.CRIT_DAMAGE_BONUS),
    ],
    spell_icon_id=2168,
    notes='HOLY.md 7,3: rank 1 - spell criticals deal 165% damage (SPELLMOD_CRIT_DAMAGE_BONUS +30%, '
          'base_points=29), scoped to Smite|HF|Holy Nova dmg|Penance dmg bolt|Chastise|Halo|Divine Star.',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spell criticals deal $s1% damage.\n\n|cFF9D9D9DCapstone Bonus: Direct damaging criticals increase the crit chance of your next Holy spell by 4%, stacking up to 5 times, once per sec. Damaging Holy criticals have a chance to increase magic damage done by 5% for 8 sec.|r', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': _HOLY_WRATH_DMG_MASK[0], 'EffectSpellClassMaskA_3': _HOLY_WRATH_DMG_MASK[2], 'EffectChainAmplitude_1': 1.0},
)


holy_wrath_200211 = spell(
    id=200211,
    name='Holy Wrath',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=59, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.CRIT_DAMAGE_BONUS),
    ],
    spell_icon_id=2168,
    notes='HOLY.md 7,3: rank 2, criticals deal 180% (base_points=59).',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spell criticals deal $s1% damage.\n\n|cFF9D9D9DCapstone Bonus: Direct damaging criticals increase the crit chance of your next Holy spell by 4%, stacking up to 5 times, once per sec. Damaging Holy criticals have a chance to increase magic damage done by 5% for 8 sec.|r', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': _HOLY_WRATH_DMG_MASK[0], 'EffectSpellClassMaskA_3': _HOLY_WRATH_DMG_MASK[2], 'EffectChainAmplitude_1': 1.0},
)


holy_wrath_200212 = spell(
    id=200212,
    name='Holy Wrath',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.CRIT_DAMAGE_BONUS),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2168,
    notes='HOLY.md 7,3: rank 3 (final kept rank), criticals deal 200% (base_points=99), plus the '
          'capstone (eff2 hidden DUMMY marker, read by spell_pri_holy_wrath_capstone). procs_on '
          'below has no spell_proc Cooldown - the 1 s crit-stack gate and the separate magic-damage '
          'roll are both script-side so they gate independently. Tooltip capstone line, final rank '
          'plain color.',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spell criticals deal $s1% damage.\n\nCapstone Bonus: Direct damaging criticals increase the crit chance of your next Holy spell by 4%, stacking up to 5 times, once per sec. Damaging Holy criticals have a chance to increase magic damage done by 5% for 8 sec.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': _HOLY_WRATH_DMG_MASK[0], 'EffectSpellClassMaskA_3': _HOLY_WRATH_DMG_MASK[2], 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0},
)
procs_on(holy_wrath_200212, PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG, hit_mask=PROC_HIT_CRITICAL, chance=100)
scripted_by(holy_wrath_200212, 'spell_pri_holy_wrath_capstone')


holy_wrath_crit_200213 = spell(
    id=200213,
    name='Holy Wrath',
    school=School.HOLY,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CRITICAL_CHANCE),
    ],
    spell_icon_id=2168,
    notes='HOLY.md 7,3: capstone clause 1 buff - +4% crit chance to Holy-school priest spells '
          '(base_points=3), StackAmount=5, ProcCharges=1 (each stack consumes one charge of the '
          'next Holy spell that crits/casts - WP-B decides the exact consume point), 5 s. Mask is '
          "the standard priest-heal family bits (Flash Heal/Heal/Greater Heal/Binding Heal/Penance/"
          'Prayer of Mending/Prayer of Healing/Circle of Healing, same as Inspiration/Test of '
          "Faith's own scoping) PLUS Smite|Holy Fire (dw1), since \"next Holy spell\" in a damage "
          "capstone's own tooltip most plausibly includes the caster's direct Holy nukes, not only heals.",
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your next Holy spell by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Next Holy spell crit chance increased.', 'EquippedItemClass': -1, 'ProcChance': 101, 'ProcCharges': 1, 'StackAmount': 5, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': 420748992, 'EffectSpellClassMaskA_2': 134283268, 'EffectSpellClassMaskA_3': 4, 'EffectChainAmplitude_1': 1.0},
)


holy_wrath_magic_dmg_200214 = spell(
    id=200214,
    name='Holy Wrath',
    school=School.HOLY,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=126),
    ],
    spell_icon_id=2168,
    notes='HOLY.md 7,3: capstone clause 2 buff - +5% magic damage done (base_points=4, misc 126 = '
          'magic schools), 8 s.',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases magic damage done by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Magic damage done increased by $s1%.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectChainAmplitude_1': 1.0},
)


# --- 8,3 Echo of Light (NEW talent 60019) ------------------------------------------------
_ECHO_HOLY_WORD_MASK = (0, 0, _masks.HW_SERENITY | _masks.HW_SANCTIFY | _masks.HW_CHASTISE)

echo_of_light_200215 = spell(
    id=200215,
    name='Echo of Light',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2382,
    notes='HOLY.md 8,3/design doc §5.1: rank 1 - eff1 Holy Words +10% effective (base_points=9), '
          'scoped HW_SERENITY|HW_SANCTIFY|HW_CHASTISE (dw3). eff2 hidden marker holding the Echo '
          "base (25% of the Holy Word's amount, base_points=24) that spell_pri_echo_of_light_heal/"
          '_damage read via GetEchoOfLightBasePct and then AddPct by Mastery. Was 250/300/350% '
          '"of Mastery" (a pure multiplier, so 0 Mastery meant no Echo at all) - changed 2026-09-22 '
          'per the user: Mastery increases the Echo, it is not a prerequisite for it.',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Holy Words are $s1% more effective. Holy Word: Serenity and Holy Word: Sanctify apply a healing Echo, and Holy Word: Chastise applies a damage Echo, for $s2% of the amount over 6 sec, increased by your Mastery.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectSpellClassMaskA_3': _ECHO_HOLY_WORD_MASK[2], 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0},
)


echo_of_light_200216 = spell(
    id=200216,
    name='Echo of Light',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2382,
    notes='HOLY.md 8,3: rank 2, +20% (base_points=19), Echo base 30% (base_points=29).',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Holy Words are $s1% more effective. Holy Word: Serenity and Holy Word: Sanctify apply a healing Echo, and Holy Word: Chastise applies a damage Echo, for $s2% of the amount over 6 sec, increased by your Mastery.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectSpellClassMaskA_3': _ECHO_HOLY_WORD_MASK[2], 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0},
)


echo_of_light_200217 = spell(
    id=200217,
    name='Echo of Light',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=34, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2382,
    notes='HOLY.md 8,3: rank 3, +30% (base_points=29), Echo base 35% (base_points=34). The '
          'only Mastery consumer in this tree (design doc §1).',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Holy Words are $s1% more effective. Holy Word: Serenity and Holy Word: Sanctify apply a healing Echo, and Holy Word: Chastise applies a damage Echo, for $s2% of the amount over 6 sec, increased by your Mastery.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectSpellClassMaskA_3': _ECHO_HOLY_WORD_MASK[2], 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0},
)


echo_of_light_heal_200218 = spell(
    id=200218,
    name='Echo of Light',
    school=School.HOLY,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.PERIODIC_HEAL, amplitude=2000),
    ],
    spell_icon_id=2382,
    notes='HOLY.md 8,3/design doc §5.1: healing Echo - 6 s, 3 ticks at a fixed 2 s interval, per-tick '
          'amount script-set (reservoir math in spell_pri_echo_of_light_heal). '
          'AttributesEx2|=SPELL_ATTR2_CANT_CRIT (0x20000000) and '
          'AttributesEx3|=SPELL_ATTR3_SUPPRESS_CASTER_PROCS|SPELL_ATTR3_SUPPRESS_TARGET_PROCS|'
          'SPELL_ATTR3_IGNORE_CASTER_MODIFIERS (0x10000|0x20000|0x20000000) implement the design '
          "doc's exemptions (cannot crit, cannot proc, snapshotted done-mods). No family bits, by "
          'design (PLAN §2: "no talent can accidentally SpellMod" the Echo).',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals the target every $t1 sec.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Healing every $t1 sec.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'AttributesEx2': 536870912, 'AttributesEx3': 536936448, 'EffectChainAmplitude_1': 1.0},
)


echo_of_light_damage_200219 = spell(
    id=200219,
    name='Echo of Light',
    school=School.HOLY,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=2000),
    ],
    spell_icon_id=2382,
    notes='HOLY.md 8,3: damage Echo, same shape as 200218 - 6 s, 3 ticks, fixed 2 s interval, '
          'same CANT_CRIT/SUPPRESS_PROCS/IGNORE_CASTER_MODIFIERS attributes, no family bits.',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Deals damage to the target every $t1 sec.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage every $t1 sec.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'AttributesEx2': 536870912, 'AttributesEx3': 536936448, 'EffectChainAmplitude_1': 1.0},
)


# --- 9,2 Epiphany of Light (NEW talent 60020) --------------------------------------------
epiphany_of_light_200220 = spell(
    id=200220,
    name='Epiphany of Light',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=33151),
    ],
    spell_icon_id=1876,
    notes='HOLY.md 9,2: rank 1 - eff1 SPELLMOD_DOT +20% (base_points=19) scoped Holy Fire. eff2 '
          'procs Surge of Light (33151) at 2% chance (procs_on below), 5 s internal lockout.',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the periodic damage of your Holy Fire by $s1%, and gives it a 2% chance to trigger Surge of Light. Once per 5 sec.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': _masks.HOLY_FIRE, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0},
)
procs_on(epiphany_of_light_200220, PROC_FLAG_DONE_PERIODIC, family_name=6, family_mask=(_masks.HOLY_FIRE, 0, 0),
         spell_type_mask=PROC_SPELL_TYPE_DAMAGE, chance=2, cooldown_ms=5000)


epiphany_of_light_200221 = spell(
    id=200221,
    name='Epiphany of Light',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=33151),
    ],
    spell_icon_id=1876,
    notes='HOLY.md 9,2: rank 2, +40% (base_points=39), 4% chance.',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the periodic damage of your Holy Fire by $s1%, and gives it a 4% chance to trigger Surge of Light. Once per 5 sec.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': _masks.HOLY_FIRE, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0},
)
procs_on(epiphany_of_light_200221, PROC_FLAG_DONE_PERIODIC, family_name=6, family_mask=(_masks.HOLY_FIRE, 0, 0),
         spell_type_mask=PROC_SPELL_TYPE_DAMAGE, chance=4, cooldown_ms=5000)


epiphany_of_light_200222 = spell(
    id=200222,
    name='Epiphany of Light',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=59, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=33151),
    ],
    spell_icon_id=1876,
    notes='HOLY.md 9,2: rank 3, +60% (base_points=59), 6% chance.',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the periodic damage of your Holy Fire by $s1%, and gives it a 6% chance to trigger Surge of Light. Once per 5 sec.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': _masks.HOLY_FIRE, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0},
)
procs_on(epiphany_of_light_200222, PROC_FLAG_DONE_PERIODIC, family_name=6, family_mask=(_masks.HOLY_FIRE, 0, 0),
         spell_type_mask=PROC_SPELL_TYPE_DAMAGE, chance=6, cooldown_ms=5000)


# --- 9,3 Holy Word: Chastise buff --------------------------------------------------------
chastise_buff_200224 = spell(
    id=200224,
    name='Chastise',
    school=School.HOLY,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=90104,
    notes='HOLY.md 9,3/§2 "Chastise follow-up": +30% Smite/Holy Fire damage (base_points=29), 10 s, '
          'applied by Holy Word: Chastise\'s own effect_2 TRIGGER_SPELL (self).',
    raw_overrides={'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your next Smite or Holy Fire by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Smite and Holy Fire damage increased by $s1%.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': _masks.SMITE | _masks.HOLY_FIRE, 'EffectChainAmplitude_1': 1.0},
)


# --- Halo healing-taken buff (baseline edit, HOLY.md "Halo healing-taken") --------------
halo_healing_taken_200173 = spell(
    id=200173,
    name='Halo',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    duration_ms=10000,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=21, apply_aura=AuraType.MOD_HEALING_RECEIVED),
    ],
    spell_icon_id=90102,
    notes='HOLY.md "Halo healing-taken"/design doc §3: +10% Holy healing received from the caster '
          '(base_points=9), 10 s - mirrors stock Grace\'s (47930) exact shape: MOD_HEALING_RECEIVED '
          '(283) lives on effect_2 (letter B) with effect_1 empty, and the caster-scoping ("from '
          'that caster only") is native to the aura (Unit.cpp:9607-9613 checks '
          'caster->GetGUID()==aurEff->GetCasterGUID(), confirmed by reading '
          'Unit::SpellHealingBonusTaken before writing this row, per the plan\'s instruction) - no '
          'script needed for that part. Classmask (letter B = effect index 2) reuses Grace\'s own '
          '"all priest healing spells" mask verbatim: 283 has no school-restriction knob of its '
          'own (confirmed by reading HandleAuraModHealingReceived/SpellHealingBonusTaken - it '
          'checks caster GUID and classmask only, never SpellSchoolMask), so "Holy healing" is '
          'realized via the priest-heal family bits rather than an actual school filter, same '
          'approach the codebase already uses for Grace. Cast by spell_pri_halo_pulse (WP-B, '
          'spell_priest_new.cpp) on each target Halo heals.',
    raw_overrides={'AttributesEx3': 262272, 'AttributesEx5': 32, 'AttributesEx7': 268435456, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases Holy healing received from the caster by $s2%.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Healing received from the caster increased by $s2%.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'EffectDieSides_1': 1, 'EffectBasePoints_1': -1, 'EffectSpellClassMaskB_1': 423894593, 'EffectSpellClassMaskB_2': 65572, 'EffectSpellClassMaskB_3': 2147500036, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0},
)
