"""
Hunter - player-castable spells (real cast_time_ms/cooldown_ms, not marked passive).

Split from a single source/classes/hunter.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .hunter_...` below) resolve.
"""

from lib.dsl import AuraType, DispelType, Effect, EffectType, Mechanic, PowerType, School
from lib.dsl.registry import spell
from .hunter_trigger_spells import volley_42243


mend_pet_136 = spell(
    id=136,
    name='Mend Pet',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=9,
    range_yards=45.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, points_per_level=15.073529411764707, implicit_target_a=5, apply_aura=AuraType.PERIODIC_HEAL, amplitude=3000),
    ],
    spell_icon_id=267,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 12); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 10 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx4': 64, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Heals $s1 every $t1 sec.', 'BaseLevel': 12, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31756, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals your pet for $<total> health over $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 8388608, 'SpellClassSet': 9, 'SpellDescriptionVariableID': 31, 'SpellLevel': 12, 'SpellPriority': 50, 'SpellVisualID_1': 652, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetCreatureType': 1},
)


disengage_781 = spell(
    id=781,
    name='Disengage',
    school=School.NORMAL,
    attributes=1376256,
    cast_time_ms=0,
    cooldown_ms=25000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=50000.0,
    effects=[
        Effect(type=138, base_points=74, implicit_target_a=1, misc_value=200),
    ],
    spell_icon_id=539,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 67108864, 'AttributesEx3': 1073938432, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'You attempt to disengage from combat, leaping backwards.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You attempt to disengage from combat, leaping backwards. Can only be used while in combat.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassMask_2': 16384, 'SpellClassSet': 9, 'SpellLevel': 20, 'SpellVisualID_1': 12305},
)


eyes_of_the_beast_1002 = spell(
    id=1002,
    name='Eyes of the Beast',
    school=School.NATURE,
    attributes=1114112,
    cast_time_ms=2000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=1,
    range_yards=50000.0,
    duration_ms=60000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=5, apply_aura=128, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=5, apply_aura=79, misc_value=127),
    ],
    spell_icon_id=49,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 67248132, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Directly controlling pet.', 'BaseLevel': 14, 'CastingTimeIndex': 5, 'ChannelInterruptFlags': 27692, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Take direct control of your pet and see through its eyes for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 4194304, 'SpellClassSet': 9, 'SpellLevel': 14, 'SpellPriority': 50, 'SpellVisualID_1': 6039, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetCreatureType': 1},
)


hunter_s_mark_1130 = spell(
    id=1130,
    name="Hunter's Mark",
    school=School.ARCANE,
    dispel=DispelType.MAGIC,
    attributes=67174400,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=2,
    range_yards=100.0,
    duration_ms=300000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=68),
        Effect(type=EffectType.APPLY_AURA, base_points=19, points_per_level=6.486486486486487, implicit_target_a=6, apply_aura=127),
    ],
    spell_icon_id=538,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 6); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx3': 196609, 'AttributesEx4': 1048576, 'AttributesEx5': 32, 'AttributesEx6': 4, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'All attackers gain $s2 ranged attack power against this target.', 'BaseLevel': 6, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Places the Hunter's Mark on the target, increasing the ranged attack power of all attackers against that target by $s2.  In addition, the target of this ability can always be seen by the hunter whether it stealths or turns invisible.  The target also appears on the mini-map.  Lasts for $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassMask_1': 1024, 'SpellClassSet': 9, 'SpellLevel': 6, 'SpellPriority': 50, 'SpellVisualID_1': 3239, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


track_beasts_1494 = spell(
    id=1494,
    name='Track Beasts',
    school=School.NORMAL,
    attributes=151257104,
    category=1239,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=1500,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=44, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=168, misc_value=127),
    ],
    spell_icon_id=179,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268566560, 'AttributesEx3': 1048576, 'AttributesEx4': 2097152, 'AttributesEx6': 4096, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Tracking Beasts.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shows the location of all nearby beasts on the minimap.  Only one form of tracking can be active at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_3': 2, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellVisualID_1': 316, 'StartRecoveryCategory': 133},
)


mongoose_bite_1495 = spell(
    id=1495,
    name='Mongoose Bite',
    school=School.NORMAL,
    attributes=327680,
    category=65,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=5000,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=24, points_per_level=3.984375, implicit_target_a=6),
    ],
    spell_icon_id=257,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 16); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 16, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Attack the enemy for ${$AP*0.2+$m1} damage.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 2, 'SpellClassSet': 9, 'SpellLevel': 16, 'SpellVisualID_1': 342, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


freezing_trap_1499 = spell(
    id=1499,
    name='Freezing Trap',
    school=School.FROST,
    attributes=65536,
    category=411,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=30000,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=0.0,
    duration_ms=30000,
    effects=[
        Effect(type=104, die_sides=0, implicit_target_a=47, misc_value=2561, radius_yards=2.0),
    ],
    spell_icon_id=180,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Place a frost trap that freezes the first enemy that approaches, preventing all action for up to $3355d.  Any damage caused will break the ice.  Trap will exist for $d.  Only one trap can be active at a time.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 128, 'SpellClassSet': 9, 'SpellLevel': 20, 'SpellVisualID_1': 3302, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


volley_1510 = spell(
    id=1510,
    name='Volley',
    school=School.ARCANE,
    attributes=4259842,
    category=49,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=17,
    range_yards=35.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.PERSISTENT_AREA_AURA, base_points=49, points_per_level=1.5, implicit_target_a=28, apply_aura=AuraType.DUMMY, radius_yards=8.0),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=1000, trigger_spell=volley_42243.id),
    ],
    spell_icon_id=126,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 40); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 268435612, 'AttributesEx2': 4325376, 'AttributesEx3': 32, 'AttributesEx4': 134217728, 'AttributesEx5': 8192, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 40, 'CastingTimeIndex': 18, 'ChannelInterruptFlags': 31756, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Continuously fires a volley of ammo at the target area, causing ${$RAP*0.083700+$42243m1} Arcane damage to enemy targets within $a1 yards every ${$1510d/6}.2 $Lsecond:seconds; for $1510d.', 'EffectBonusMultiplier_1': 0.14300000667572021, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 262156, 'ImplicitTargetA_3': 1, 'InterruptFlags': 9, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'Speed': 30.0, 'SpellClassMask_1': 8192, 'SpellClassSet': 9, 'SpellLevel': 40, 'SpellVisualID_1': 10384, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Targets': 64},
)


scare_beast_1513 = spell(
    id=1513,
    name='Scare Beast',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    mechanic=Mechanic.FEAR,
    attributes=1073807360,
    category=33,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=30000,
    mana_cost=0,
    mana_cost_pct=2,
    range_yards=30.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=AuraType.MOD_FEAR),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=6, apply_aura=AuraType.MOD_INCREASE_SPEED),
    ],
    spell_icon_id=958,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 14); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx5': 32, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Feared.', 'BaseLevel': 14, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Scares a beast, causing it to run in fear for up to $d.  Damage caused may interrupt the effect.  Only one beast can be feared at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 664232, 'SpellClassMask_2': 65536, 'SpellClassSet': 9, 'SpellLevel': 14, 'SpellVisualID_1': 336, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetCreatureType': 1},
)


flare_1543 = spell(
    id=1543,
    name='Flare',
    school=School.ARCANE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=20000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=2,
    range_yards=30.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.PERSISTENT_AREA_AURA, base_points=-1, implicit_target_a=28, apply_aura=41, misc_value=5, radius_yards=10.0),
        Effect(type=EffectType.PERSISTENT_AREA_AURA, base_points=-1, implicit_target_a=28, apply_aura=41, misc_value=6, radius_yards=10.0),
    ],
    spell_icon_id=136,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 164864, 'AttributesEx2': 4194304, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Hidden and invisible units are revealed.', 'BaseLevel': 32, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Exposes all hidden and invisible enemies within $a1 yards of the targeted area for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 5.0, 'SpellClassMask_2': 32768, 'SpellClassSet': 9, 'SpellLevel': 32, 'SpellVisualID_1': 10387, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Targets': 64},
)


serpent_sting_1978 = spell(
    id=1978,
    name='Serpent Sting',
    school=School.NATURE,
    dispel=DispelType.POISON,
    attributes=65538,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=9,
    range_yards=35.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, points_per_level=3.1315789473684212, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=271, misc_value=127),
    ],
    spell_icon_id=536,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 4); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 12 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 131072, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Causes $s1 Nature damage every $t1 seconds.', 'BaseLevel': 4, 'CastingTimeIndex': 18, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Stings the target, causing ${$RAP*0.2+$m1*$d/3} Nature damage over $d.  Only one Sting per Hunter can be active on any one target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 162311, 'EffectSpellClassMaskB_2': 2290221313, 'EffectSpellClassMaskB_3': 246273, 'EquippedItemClass': 2, 'EquippedItemSubclass': 262156, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'ModalNextSpell': 75, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 114, 'Speed': 40.0, 'SpellClassMask_1': 16384, 'SpellClassSet': 9, 'SpellLevel': 4, 'SpellVisualID_1': 3179, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


multi_shot_2643 = spell(
    id=2643,
    name='Multi-Shot',
    school=School.NORMAL,
    attributes=65538,
    category=85,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    mana_cost=0,
    mana_cost_pct=9,
    range_yards=35.0,
    effects=[
        Effect(type=121, points_per_level=6.564516129032258, die_sides=0, implicit_target_a=6, chain_targets=3),
    ],
    spell_icon_id=85,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 18); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 8 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 131072, 'AttributesEx5': 32768, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 18, 'CastingTimeIndex': 1, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Fires several missiles, hitting $x1 targets.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 262156, 'FacingCasterFlags': 1, 'InterruptFlags': 9, 'MaxLevel': 80, 'ModalNextSpell': 75, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 114, 'Speed': 30.0, 'SpellClassMask_1': 4096, 'SpellClassSet': 9, 'SpellLevel': 18, 'SpellPriority': 50, 'SpellVisualID_1': 567, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


growl_2649 = spell(
    id=2649,
    name='Growl',
    school=School.NORMAL,
    attributes=65536,
    category=82,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=5000,
    power_type=PowerType.FOCUS,
    mana_cost=15,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.THREAT, base_points=49, points_per_level=14.987341772151899, implicit_target_a=6),
    ],
    spell_icon_id=201,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AttributesEx2': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your pet growls at the target, generating threat and increasing the likelihood the target will attack it.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellVisualID_1': 34},
)


raptor_strike_2973 = spell(
    id=2973,
    name='Raptor Strike',
    school=School.NORMAL,
    attributes=328708,
    category=40,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=6000,
    mana_cost=0,
    mana_cost_pct=4,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.WEAPON_DAMAGE, base_points=4, points_per_level=4.177215189873418, implicit_target_a=6),
    ],
    spell_icon_id=26,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 11 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A strong attack that increases melee damage by $s1.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 2, 'SpellClassMask_3': 65536, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellPriority': 50, 'SpellVisualID_1': 39},
)


wing_clip_2974 = spell(
    id=2974,
    name='Wing Clip',
    school=School.NORMAL,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=5.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-51, mechanic=Mechanic.SNARE, implicit_target_a=6, apply_aura=AuraType.MOD_DECREASE_SPEED),
    ],
    spell_icon_id=517,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 512, 'AttributesEx3': 1032, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement speed reduced by $s1%.', 'BaseLevel': 12, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Maims the enemy, reducing the target's movement speed by $s1% for $d.", 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 64, 'SpellClassSet': 9, 'SpellLevel': 12, 'SpellPriority': 50, 'SpellVisualID_1': 556, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


viper_sting_3034 = spell(
    id=3034,
    name='Viper Sting',
    school=School.NATURE,
    dispel=DispelType.POISON,
    attributes=65538,
    category=1175,
    cooldown_ms=0,
    category_cooldown_ms=15000,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=35.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=6, apply_aura=64, amplitude=2000),
    ],
    spell_icon_id=253,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 131072, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Drains $m1% mana every $t1 seconds, restoring 300% of the amount drained to the Hunter.', 'BaseLevel': 36, 'CastingTimeIndex': 18, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Stings the target, draining ${$m1*4}% mana over $d (up to a maximum of ${$m1*2*4}% of the caster's maximum mana), and energizing the Hunter equal to 300% of the amount drained.  Only one Sting per Hunter can be active on any one target.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 3.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 262156, 'FacingCasterFlags': 1, 'ModalNextSpell': 75, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 114, 'Speed': 40.0, 'SpellClassMask_2': 128, 'SpellClassSet': 9, 'SpellLevel': 36, 'SpellVisualID_1': 3181, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


scorpid_sting_3043 = spell(
    id=3043,
    name='Scorpid Sting',
    school=School.NATURE,
    dispel=DispelType.POISON,
    attributes=65538,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=11,
    range_yards=35.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-4, implicit_target_a=6, apply_aura=54),
    ],
    spell_icon_id=256,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 131072, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Chance to hit with melee and ranged attacks reduced by $s1%.', 'BaseLevel': 22, 'CastingTimeIndex': 18, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Stings the target, reducing chance to hit with melee and ranged attacks by $s1% for $d.  Only one Sting per Hunter can be active on any one target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 262156, 'FacingCasterFlags': 1, 'ModalNextSpell': 75, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 114, 'Speed': 40.0, 'SpellClassMask_1': 32768, 'SpellClassSet': 9, 'SpellLevel': 22, 'SpellVisualID_1': 3219, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


arcane_shot_3044 = spell(
    id=3044,
    name='Arcane Shot',
    school=School.ARCANE,
    attributes=65538,
    category=1173,
    cooldown_ms=0,
    category_cooldown_ms=6000,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=35.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=14, points_per_level=6.445945945945946, implicit_target_a=6),
    ],
    spell_icon_id=218,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 6); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 11 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 131072, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 6, 'CastingTimeIndex': 18, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'An instant shot that causes ${$RAP*0.15+$m1} Arcane damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 262156, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'ModalNextSpell': 75, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 114, 'Speed': 40.0, 'SpellClassMask_1': 2048, 'SpellClassSet': 9, 'SpellLevel': 6, 'SpellVisualID_1': 3299, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


rapid_fire_3045 = spell(
    id=3045,
    name='Rapid Fire',
    school=School.NORMAL,
    attributes=262160,
    category=55,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=300000,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=140),
    ],
    spell_icon_id=537,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases ranged attack speed by $s1%.', 'BaseLevel': 26, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases ranged attack speed by $s1% for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 32, 'SpellClassSet': 9, 'SpellLevel': 26, 'SpellVisualID_1': 13245},
)


aspect_of_the_cheetah_5118 = spell(
    id=5118,
    name='Aspect of the Cheetah',
    school=School.NATURE,
    attributes=329728,
    category=47,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=1000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.MOD_INCREASE_SPEED),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=15571),
    ],
    spell_icon_id=1181,
    notes='pulled from existing data',
    raw_overrides={'ActiveIconID': 122, 'AttributesEx': 131072, 'AttributesEx3': 67108864, 'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s1% increased movement speed.  Dazed if struck.', 'AuraInterruptFlags': 131072, 'BaseLevel': 16, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The hunter takes on the aspects of a cheetah, increasing movement speed by $s1%.  If the hunter is struck, $ghe:she; will be dazed for $15571d.  Only one Aspect can be active at a time.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 139944, 'RangeIndex': 1, 'SpellClassMask_1': 2097152, 'SpellClassSet': 9, 'SpellLevel': 16, 'SpellVisualID_1': 3719},
)


aspect_of_the_pack_13159 = spell(
    id=13159,
    name='Aspect of the Pack',
    school=School.NATURE,
    attributes=329728,
    category=47,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=1000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=65, base_points=29, implicit_target_a=1, apply_aura=AuraType.MOD_INCREASE_SPEED, radius_yards=40.0),
        Effect(type=65, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=15571, radius_yards=40.0),
    ],
    spell_icon_id=916,
    notes='pulled from existing data',
    raw_overrides={'ActiveIconID': 122, 'AttributesEx': 131072, 'AttributesEx3': 67108864, 'AttributesEx4': 524288, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s1% increased movement speed.  Dazed if struck.', 'AuraInterruptFlags': 131072, 'BaseLevel': 40, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The hunter and raid members within $a1 yards take on the aspects of a pack of cheetahs, increasing movement speed by $s1%.  If you are struck under the effect of this aspect, you will be dazed for $15571d.  Only one Aspect can be active at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 139944, 'RangeIndex': 1, 'SpellClassMask_1': 2097152, 'SpellClassSet': 9, 'SpellLevel': 40, 'SpellVisualID_1': 3405},
)


aspect_of_the_beast_13161 = spell(
    id=13161,
    name='Aspect of the Beast',
    school=School.NATURE,
    attributes=327680,
    category=47,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=1000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=120),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=166),
    ],
    spell_icon_id=1510,
    notes='pulled from existing data',
    raw_overrides={'ActiveIconID': 122, 'AttributesEx': 131072, 'AttributesEx3': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Untrackable and melee attack power for the pet and hunter increased by 10%.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "The hunter takes on the aspects of a beast, becoming untrackable and increasing melee attack power of the hunter and the hunter's pet by $m2%.  Only one Aspect can be active at a time.", 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_3': 16, 'SpellClassSet': 9, 'SpellDescriptionVariableID': 4294967295, 'SpellLevel': 30, 'SpellVisualID_1': 3139},
)


aspect_of_the_monkey_13163 = spell(
    id=13163,
    name='Aspect of the Monkey',
    school=School.NATURE,
    attributes=327680,
    category=47,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=1000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=17, implicit_target_a=1, apply_aura=49),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=60798),
    ],
    spell_icon_id=1549,
    notes='pulled from existing data',
    raw_overrides={'ActiveIconID': 122, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases chance to dodge by $s1%.', 'BaseLevel': 4, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The hunter takes on the aspects of a monkey, increasing chance to dodge by $s1%.  Only one Aspect can be active at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcTypeMask': 680, 'RangeIndex': 1, 'SpellClassMask_1': 524288, 'SpellClassSet': 9, 'SpellLevel': 4, 'SpellVisualID_1': 3140},
)


aspect_of_the_hawk_13165 = spell(
    id=13165,
    name='Aspect of the Hawk',
    school=School.NATURE,
    attributes=327680,
    category=47,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=1000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, points_per_level=2.0, implicit_target_a=1, apply_aura=124),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=6150),
    ],
    spell_icon_id=112,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1->covers-60 (anchor rank 7 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'ActiveIconID': 122, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases ranged attack power by $s1.', 'BaseLevel': 10, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The hunter takes on the aspects of a hawk, increasing ranged attack power by $s1.  Only one Aspect can be active at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassMask_1': 1048576, 'SpellClassSet': 9, 'SpellLevel': 10, 'SpellVisualID_1': 3161},
)


immolation_trap_13795 = spell(
    id=13795,
    name='Immolation Trap',
    school=School.FIRE,
    attributes=65536,
    category=1250,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=30000,
    mana_cost=0,
    mana_cost_pct=9,
    range_yards=0.0,
    duration_ms=30000,
    effects=[
        Effect(type=105, die_sides=0, implicit_target_a=47, misc_value=164638, radius_yards=2.0),
    ],
    spell_icon_id=678,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 16); RealPointsPerLevel from rank1->covers-60 (anchor rank 5 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 16, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Place a fire trap that will burn the first enemy to approach for ${($RAP*($<mult>/100)+$13797m1)*$<duration>} Fire damage over $13797d.  Trap will exist for $d.  Only one trap can be active at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 128, 'SpellClassSet': 9, 'SpellDescriptionVariableID': 121, 'SpellLevel': 16, 'SpellVisualID_1': 3302, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


frost_trap_13809 = spell(
    id=13809,
    name='Frost Trap',
    school=School.FROST,
    attributes=65536,
    category=411,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=30000,
    mana_cost=0,
    mana_cost_pct=2,
    range_yards=0.0,
    duration_ms=30000,
    effects=[
        Effect(type=104, die_sides=0, implicit_target_a=47, misc_value=164639, radius_yards=2.0),
    ],
    spell_icon_id=56,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 28, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Place a frost trap that creates an ice slick around itself for $13810d when the first enemy approaches it.  All enemies within $13810a1 yards will be slowed by $13810s1% while in the area of effect.  Trap will exist for $13809d.  Only one trap can be active at a time.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 128, 'SpellClassSet': 9, 'SpellLevel': 28, 'SpellVisualID_1': 3302, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


explosive_trap_13813 = spell(
    id=13813,
    name='Explosive Trap',
    school=School.FIRE,
    attributes=65536,
    category=1250,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=30000,
    mana_cost=0,
    mana_cost_pct=19,
    range_yards=0.0,
    duration_ms=30000,
    effects=[
        Effect(type=105, die_sides=0, implicit_target_a=47, misc_value=164839, radius_yards=2.0),
    ],
    spell_icon_id=37,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 34); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 34, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Place a fire trap that explodes when an enemy approaches, causing ${$RAP*0.1+$13812m1} to ${$RAP*0.1+$13812M1} Fire damage and burning all enemies for ${$13812m2*10+$RAP} additional Fire damage over $13812d to all within $13812a1 yards.  Trap will exist for $13813d.  Only one trap can be active at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 128, 'SpellClassSet': 9, 'SpellLevel': 34, 'SpellVisualID_1': 3302, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


claw_16827 = spell(
    id=16827,
    name='Claw',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=25,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=3, points_per_level=1.4430379746835442, die_sides=3, implicit_target_a=6),
    ],
    spell_icon_id=262,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 11 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Claw the enemy, causing $s1 damage.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellVisualID_1': 6762, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


bite_17253 = spell(
    id=17253,
    name='Bite',
    school=School.NORMAL,
    attributes=327696,
    category=19,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=25,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=3, points_per_level=1.4430379746835442, die_sides=3, implicit_target_a=6),
    ],
    spell_icon_id=1680,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 11 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Bite the enemy, causing $s1 damage.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellVisualID_1': 376, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


deterrence_19263 = spell(
    id=19263,
    name='Deterrence',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=90000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=47),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=287),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MOD_PACIFY),
    ],
    spell_icon_id=83,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 16, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Parry chance increased by $s1%, chance for ranged attacks to miss you increased by $s2%, $s2% chance to deflect spells, and unable to attack.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When activated, increases parry chance by $s1%, reduces the chance ranged attacks will hit you by $s1% and grants a $s2% chance to deflect spells.  While Deterrence is active, you cannot attack.  Lasts $d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 2, 'SpellClassSet': 9, 'SpellLevel': 60, 'SpellVisualID_1': 14246},
)


tranquilizing_shot_19801 = spell(
    id=19801,
    name='Tranquilizing Shot',
    school=School.NATURE,
    attributes=65538,
    cooldown_ms=8000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=35.0,
    effects=[
        Effect(type=EffectType.DISPEL, implicit_target_a=6, misc_value=9),
        Effect(type=EffectType.DISPEL, implicit_target_a=6, misc_value=1),
    ],
    spell_icon_id=155,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 131072, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 18, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Attempts to remove $s1 Enrage and $s2 Magic effect from an enemy target.', 'EffectBasePoints_3': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': 2, 'EquippedItemSubclass': 262156, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 114, 'Speed': 40.0, 'SpellClassMask_1': 65536, 'SpellClassMask_3': 256, 'SpellClassSet': 9, 'SpellLevel': 60, 'SpellVisualID_1': 560, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


track_demons_19878 = spell(
    id=19878,
    name='Track Demons',
    school=School.NORMAL,
    attributes=151257104,
    category=1239,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=1500,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=44, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=168, misc_value=127),
    ],
    spell_icon_id=214,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268566560, 'AttributesEx3': 1048576, 'AttributesEx4': 2097152, 'AttributesEx6': 4096, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Tracking Demons.', 'BaseLevel': 32, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shows the location of all nearby demons on the minimap.  Only one form of tracking can be active at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_3': 2, 'SpellClassSet': 9, 'SpellLevel': 32, 'SpellVisualID_1': 316, 'StartRecoveryCategory': 133},
)


track_dragonkin_19879 = spell(
    id=19879,
    name='Track Dragonkin',
    school=School.NORMAL,
    attributes=151257104,
    category=1239,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=1500,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=44, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=168, misc_value=127),
    ],
    spell_icon_id=1548,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268566560, 'AttributesEx3': 1048576, 'AttributesEx4': 2097152, 'AttributesEx6': 4096, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Tracking Dragonkin.', 'BaseLevel': 50, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shows the location of all nearby dragonkin on the minimap.  Only one form of tracking can be active at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_3': 2, 'SpellClassSet': 9, 'SpellLevel': 50, 'SpellVisualID_1': 316, 'StartRecoveryCategory': 133},
)


track_elementals_19880 = spell(
    id=19880,
    name='Track Elementals',
    school=School.NORMAL,
    attributes=151257104,
    category=1239,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=1500,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=44, misc_value=4),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=168, misc_value=127),
    ],
    spell_icon_id=94,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268566560, 'AttributesEx3': 1048576, 'AttributesEx4': 2097152, 'AttributesEx6': 4096, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Tracking Elementals.', 'BaseLevel': 26, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shows the location of all nearby elementals on the minimap.  Only one form of tracking can be active at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_3': 2, 'SpellClassSet': 9, 'SpellLevel': 26, 'SpellVisualID_1': 316, 'StartRecoveryCategory': 133},
)


track_giants_19882 = spell(
    id=19882,
    name='Track Giants',
    school=School.NORMAL,
    attributes=151257104,
    category=1239,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=1500,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=44, misc_value=5),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=168, misc_value=127),
    ],
    spell_icon_id=84,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268566560, 'AttributesEx3': 1048576, 'AttributesEx4': 2097152, 'AttributesEx6': 4096, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Tracking Giants.', 'BaseLevel': 40, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shows the location of all nearby giants on the minimap.  Only one form of tracking can be active at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_3': 2, 'SpellClassSet': 9, 'SpellLevel': 40, 'SpellVisualID_1': 316, 'StartRecoveryCategory': 133},
)


track_humanoids_19883 = spell(
    id=19883,
    name='Track Humanoids',
    school=School.NORMAL,
    attributes=151257104,
    category=1239,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=1500,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=44, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=168, misc_value=127),
    ],
    spell_icon_id=316,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268566560, 'AttributesEx3': 1048576, 'AttributesEx4': 2097152, 'AttributesEx6': 4096, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Tracking Humanoids.', 'BaseLevel': 10, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shows the location of all nearby humanoids on the minimap.  Only one form of tracking can be active at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_3': 2, 'SpellClassSet': 9, 'SpellLevel': 10, 'SpellVisualID_1': 316, 'StartRecoveryCategory': 133},
)


track_undead_19884 = spell(
    id=19884,
    name='Track Undead',
    school=School.NORMAL,
    attributes=151257104,
    category=1239,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=1500,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=44, misc_value=6),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=168, misc_value=127),
    ],
    spell_icon_id=170,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268566560, 'AttributesEx3': 1048576, 'AttributesEx4': 2097152, 'AttributesEx6': 4096, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Tracking Undead.', 'BaseLevel': 18, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shows the location of all nearby undead on the minimap.  Only one form of tracking can be active at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_3': 2, 'SpellClassSet': 9, 'SpellLevel': 18, 'SpellVisualID_1': 316, 'StartRecoveryCategory': 133},
)


aspect_of_the_wild_20043 = spell(
    id=20043,
    name='Aspect of the Wild',
    school=School.NATURE,
    attributes=327680,
    category=47,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=1000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=65, base_points=44, points_per_level=2.5, implicit_target_a=1, apply_aura=143, misc_value=8, radius_yards=30.0),
    ],
    spell_icon_id=266,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 46); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 4 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'ActiveIconID': 122, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Nature resistance increased by $s1.', 'BaseLevel': 46, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The hunter, group and raid members within $a1 yards take on the aspect of the wild, increasing Nature resistance by $s1.  Only one Aspect can be active at a time.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 4194304, 'SpellClassSet': 9, 'SpellLevel': 46, 'SpellVisualID_1': 5522},
)


distracting_shot_20736 = spell(
    id=20736,
    name='Distracting Shot',
    school=School.ARCANE,
    mechanic=16,
    attributes=65538,
    category=911,
    cooldown_ms=0,
    category_cooldown_ms=8000,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=35.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.THREAT, base_points=109, points_per_level=1.5, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=AuraType.MOD_TAUNT),
    ],
    spell_icon_id=1499,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 131072, 'AttributesEx4': 2048, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Distracted.', 'BaseLevel': 12, 'CastingTimeIndex': 18, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Distracts the target to attack you, but has no effect if the target is already attacking you. Lasts $56559d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 262156, 'FacingCasterFlags': 1, 'MaxLevel': 19, 'ModalNextSpell': 75, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 114, 'Speed': 40.0, 'SpellClassMask_1': 65536, 'SpellClassMask_2': 131072, 'SpellClassSet': 9, 'SpellLevel': 12, 'SpellVisualID_1': 5794, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


demoralizing_screech_24423 = spell(
    id=24423,
    name='Demoralizing Screech',
    school=School.NORMAL,
    attributes=67436560,
    category=36,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    power_type=PowerType.FOCUS,
    mana_cost=20,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=6, points_per_level=0.9873417721518988, die_sides=3, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=-36, points_per_level=-6.822784810126582, implicit_target_a=22, implicit_target_b=15, apply_aura=AuraType.MOD_ATTACK_POWER, radius_yards=5.0),
    ],
    spell_icon_id=1579,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Melee attack power reduced by $s2.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Blasts a single enemy for $s1 damage and lowers the melee attack power of all enemies in melee range by $s2.  Effect lasts $d.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellVisualID_1': 7302, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


prowl_24450 = spell(
    id=24450,
    name='Prowl',
    school=School.NORMAL,
    dispel=DispelType.STEALTH,
    attributes=437583888,
    category=38,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    power_type=PowerType.FOCUS,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=149, points_per_level=2.542372881355932, implicit_target_a=1, apply_aura=16),
        Effect(type=EffectType.APPLY_AURA, base_points=-51, points_per_level=0.1694915254237288, implicit_target_a=1, apply_aura=AuraType.MOD_DECREASE_SPEED),
        Effect(type=EffectType.APPLY_AURA, base_points=19, points_per_level=0.5084745762711864, implicit_target_a=1, apply_aura=79, misc_value=65),
    ],
    spell_icon_id=495,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'ActiveIconID': 252, 'AttributesEx': 16, 'AttributesEx2': 2097152, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Stealthed.\r\nMovement speed slowed by $s2%.', 'AuraInterruptFlags': 140291, 'BaseLevel': 1, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Puts your pet in stealth mode, but slows its movement speed by $s2%. The first attack from stealth receives a $s3% bonus to damage.  Lasts until cancelled.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ExcludeCasterAuraState': 12, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'ProcCharges': 1, 'ProcTypeMask': 332116, 'RangeIndex': 1, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellVisualID_1': 184, 'StartRecoveryCategory': 1178},
)


furious_howl_24604 = spell(
    id=24604,
    name='Furious Howl',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=40000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=20,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=17, points_per_level=3.8227848101265822, implicit_target_a=20, apply_aura=AuraType.MOD_ATTACK_POWER, misc_value=1, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=17, points_per_level=3.8227848101265822, implicit_target_a=20, apply_aura=124, radius_yards=100.0),
    ],
    spell_icon_id=1573,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increased melee and ranged attack power.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases melee and ranged attack power by $s1 for the wolf and its master for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellVisualID_1': 7299},
)


scorpid_poison_24640 = spell(
    id=24640,
    name='Scorpid Poison',
    school=School.NATURE,
    dispel=DispelType.POISON,
    attributes=67436560,
    category=19,
    cast_time_ms=0,
    cooldown_ms=10000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=20,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.THREAT, base_points=4, points_per_level=-0.05063291139240506, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, points_per_level=0.24050632911392406, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=2000),
    ],
    spell_icon_id=163,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 2097664, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s2 Nature damage every $t2 sec.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Stings an enemy for $o2 Nature damage over $d.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellVisualID_1': 19, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


lightning_breath_24844 = spell(
    id=24844,
    name='Lightning Breath',
    school=School.NATURE,
    attributes=65536,
    category=2,
    cast_time_ms=0,
    cooldown_ms=10000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=20,
    mana_cost_pct=0,
    range_yards=20.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=5, points_per_level=0.9367088607594937, die_sides=3, implicit_target_a=6),
    ],
    spell_icon_id=62,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 2, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Breathes lightning, instantly dealing $s1 Nature damage to a single target.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 4, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ProcCharges': 1, 'ProcTypeMask': 40, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellVisualID_1': 173, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


multi_shot_25294 = spell(
    id=25294,
    name='Multi-Shot',
    school=School.NORMAL,
    attributes=65538,
    category=85,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    mana_cost=0,
    mana_cost_pct=9,
    range_yards=35.0,
    effects=[
        Effect(type=121, base_points=149, implicit_target_a=6, chain_targets=3),
    ],
    spell_icon_id=85,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid)',
    raw_overrides={'AttributesEx2': 131072, 'AttributesEx5': 32768, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Fires several missiles, hitting $x1 targets for an additional $s1 damage.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 262156, 'FacingCasterFlags': 1, 'InterruptFlags': 9, 'ModalNextSpell': 75, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 114, 'Speed': 30.0, 'SpellClassMask_1': 4096, 'SpellClassSet': 9, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 567, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


serpent_sting_25295 = spell(
    id=25295,
    name='Serpent Sting',
    school=School.NATURE,
    dispel=DispelType.POISON,
    attributes=65538,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=9,
    range_yards=35.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=110, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=271, misc_value=127),
    ],
    spell_icon_id=536,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid)',
    raw_overrides={'AttributesEx2': 131072, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Causes $s1 Nature damage every $t1 seconds.', 'BaseLevel': 60, 'CastingTimeIndex': 18, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Stings the target, causing ${$RAP*0.2+$m1*$d/3} Nature damage over $d.  Only one Sting per Hunter can be active on any one target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 162311, 'EffectSpellClassMaskB_2': 2290221313, 'EffectSpellClassMaskB_3': 246273, 'EquippedItemClass': 2, 'EquippedItemSubclass': 262156, 'FacingCasterFlags': 1, 'MaxLevel': 66, 'ModalNextSpell': 75, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 9', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 114, 'Speed': 40.0, 'SpellClassMask_1': 16384, 'SpellClassSet': 9, 'SpellLevel': 60, 'SpellVisualID_1': 3179, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


aspect_of_the_hawk_25296 = spell(
    id=25296,
    name='Aspect of the Hawk',
    school=School.NATURE,
    attributes=327680,
    category=47,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=1000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=119, implicit_target_a=1, apply_aura=124),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=6150),
    ],
    spell_icon_id=112,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid)',
    raw_overrides={'ActiveIconID': 122, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases ranged attack power by $s1.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The hunter takes on the aspects of a hawk, increasing ranged attack power by $s1.  Only one Aspect can be active at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 7', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassMask_1': 1048576, 'SpellClassSet': 9, 'SpellLevel': 60, 'SpellVisualID_1': 3161},
)


kill_command_34026 = spell(
    id=34026,
    name='Kill Command',
    school=School.NORMAL,
    attributes=327680,
    category=1171,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=60000,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=45.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2226,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268436480, 'AttributesEx2': 4, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 66, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Give the command to kill, increasing your pet's damage done from special attacks by ${$34027M1*3}% for $34027d.  Each special attack done by the pet reduces the damage bonus by $34027s1%.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 2048, 'SpellClassSet': 9, 'SpellLevel': 66},
)


aspect_of_the_viper_34074 = spell(
    id=34074,
    name='Aspect of the Viper',
    school=School.NATURE,
    attributes=327680,
    category=47,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=1000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=21, amplitude=3000),
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=1, apply_aura=79, misc_value=127),
    ],
    spell_icon_id=2227,
    notes='pulled from existing data',
    raw_overrides={'ActiveIconID': 122, 'AttributesEx': 1024, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your ranged and melee attacks regenerate a percentage of your base mana, but your total damage done is reduced by $s2%.  In addition, you gain $s1% of maximum mana every $t sec.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The hunter takes on the aspect of the viper, causing ranged and melee attacks to regenerate mana but reducing your total damage done by $34074s2%.  In addition, you gain $s1% of maximum mana every $t sec.  Mana gained is based on the speed of your ranged weapon. Requires a ranged weapon. Only one Aspect can be active at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 69972, 'RangeIndex': 1, 'SpellClassMask_2': 262144, 'SpellClassSet': 9, 'SpellLevel': 20, 'SpellVisualID_1': 3399},
)


misdirection_34477 = spell(
    id=34477,
    name='Misdirection',
    school=School.NORMAL,
    attributes=33619984,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=9,
    range_yards=100.0,
    duration_ms=30000,
    effects=[
        Effect(type=130, base_points=99, implicit_target_a=57),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2231,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 67634176, 'AttributesEx2': 8, 'AttributesEx3': 67108865, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Redirecting threat.', 'AuraInterruptFlags': 131072, 'BaseLevel': 70, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The current party or raid member targeted will receive the threat caused by your next damaging attack and all actions taken for $35079d afterwards.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 100, 'ProcTypeMask': 2167124, 'SpellClassMask_2': 1048576, 'SpellClassSet': 9, 'SpellLevel': 70, 'SpellVisualID_1': 8373, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


snake_trap_34600 = spell(
    id=34600,
    name='Snake Trap',
    school=School.FIRE,
    attributes=65536,
    category=1249,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=30000,
    mana_cost=0,
    mana_cost_pct=9,
    range_yards=0.0,
    duration_ms=30000,
    effects=[
        Effect(type=106, die_sides=0, implicit_target_a=47, misc_value=183957, radius_yards=2.0),
    ],
    spell_icon_id=2295,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 68, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Place a trap that will release several venomous snakes to attack the first enemy to approach.  The snakes will die after $57879d.  Trap will exist for $d.  Only one trap can be active at a time.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 128, 'SpellClassSet': 9, 'SpellLevel': 68, 'SpellVisualID_1': 3302, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


fire_breath_34889 = spell(
    id=34889,
    name='Fire Breath',
    school=School.FIRE,
    attributes=65536,
    category=2,
    cast_time_ms=0,
    cooldown_ms=10000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=20,
    mana_cost_pct=0,
    range_yards=20.0,
    duration_ms=2000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=2, points_per_level=0.5063291139240507, die_sides=3, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, points_per_level=0.26582278481012656, die_sides=3, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=1000),
    ],
    spell_icon_id=2128,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AttributesEx2': 536870912, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Fire damage every $t second.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 2, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Breathes Fire on the target for $s1 damage plus $o2 damage over $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 5, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ProcTypeMask': 40, 'SpellClassMask_2': 268436480, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellVisualID_1': 8256, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


gore_35290 = spell(
    id=35290,
    name='Gore',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=10000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=20,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=8, points_per_level=1.4303797468354431, die_sides=3, implicit_target_a=6),
    ],
    spell_icon_id=1578,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your boar gores the enemy for $35290s1.  Causes double damage if used within 6 sec of a Charge.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'ImplicitTargetA_2': 6, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellVisualID_1': 6762, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


poison_spit_35387 = spell(
    id=35387,
    name='Poison Spit',
    school=School.NATURE,
    dispel=DispelType.POISON,
    attributes=65536,
    category=18,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    power_type=PowerType.FOCUS,
    mana_cost=20,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, points_per_level=0.31645569620253167, die_sides=3, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=2000),
        Effect(type=EffectType.APPLY_AURA, base_points=-26, implicit_target_a=6, apply_aura=216),
    ],
    spell_icon_id=68,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AttributesEx5': 512, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Nature damage inflicted every $t1 sec.\r\nCasting speed slowed by $s2%.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Spits poison at an enemy, dealing $o1 Nature damage over $d and reduces the target's casting speed by $s2% for $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 9, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 40.0, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellVisualID_1': 7910, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


smack_49966 = spell(
    id=49966,
    name='Smack',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=25,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=3, points_per_level=1.4430379746835442, die_sides=3, implicit_target_a=6),
    ],
    spell_icon_id=473,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 11 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Smack the enemy, causing $s1 damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellVisualID_1': 6762, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


pin_50245 = spell(
    id=50245,
    name='Pin',
    school=School.NORMAL,
    dispel=DispelType.MAGIC,
    mechanic=Mechanic.ROOT,
    attributes=1073741840,
    cast_time_ms=0,
    cooldown_ms=40000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=4000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_ROOT),
        Effect(type=EffectType.APPLY_AURA, points_per_level=0.34177215189873417, die_sides=3, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=1000),
    ],
    spell_icon_id=2679,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 516, 'AttributesEx5': 32, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Pinned in place.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Pins the target in place, and squeezes for $o2 damage over $d.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 100, 'RangeIndex': 2, 'ShapeshiftExclude': 2, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellVisualID_1': 5287},
)


swipe_50256 = spell(
    id=50256,
    name='Swipe',
    school=School.NORMAL,
    attributes=262160,
    category=85,
    cast_time_ms=0,
    cooldown_ms=5000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=20,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=5, points_per_level=1.0632911392405062, die_sides=3, implicit_target_a=6, chain_targets=1000),
    ],
    spell_icon_id=1562,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AttributesEx2': 4096, 'AttributesEx5': 32768, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Swipe nearby enemies, inflicting $s1 damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellVisualID_1': 189, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


tendon_rip_50271 = spell(
    id=50271,
    name='Tendon Rip',
    school=School.NORMAL,
    mechanic=Mechanic.SNARE,
    attributes=263184,
    category=36,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=20000,
    power_type=PowerType.FOCUS,
    mana_cost=20,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=6, apply_aura=AuraType.MOD_DECREASE_SPEED),
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=1, points_per_level=0.5949367088607594, die_sides=3, implicit_target_a=6),
    ],
    spell_icon_id=138,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement speed reduced by $s1%.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Tears at an enemy's legs for $s2 damage and reduces movement speed by $s1% for $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellVisualID_1': 842},
)


spore_cloud_50274 = spell(
    id=50274,
    name='Spore Cloud',
    school=School.NATURE,
    attributes=16,
    cast_time_ms=0,
    cooldown_ms=10000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=20,
    mana_cost_pct=0,
    range_yards=6.0,
    duration_ms=9000,
    effects=[
        Effect(type=EffectType.PERSISTENT_AREA_AURA, points_per_level=0.26582278481012656, die_sides=3, implicit_target_a=53, implicit_target_b=16, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000, radius_yards=6.0),
        Effect(type=EffectType.PERSISTENT_AREA_AURA, base_points=-4, implicit_target_a=28, apply_aura=101, misc_value=1, radius_yards=6.0),
    ],
    spell_icon_id=2681,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AttributesEx3': 262144, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Nature damage inflicted every $t1 sec.\r\nArmor reduced by $s2%.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Dusts nearby enemies with spores causing $s1 Nature damage every $t1 sec for $d and reducing armor by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 31, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellVisualID_1': 10409, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


serenity_dust_50318 = spell(
    id=50318,
    name='Serenity Dust',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, points_per_level=1.9873417721518987, die_sides=3, implicit_target_a=1, apply_aura=AuraType.PERIODIC_HEAL, amplitude=3000),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=166),
    ],
    spell_icon_id=1714,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx3': 128, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Attack power increased by $s2%.\r\nHealing $s1 damage every $t1 seconds.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "The moth's wings produce a cloud of dust that increases its attack power by $s2% and heals it for $o1 over $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 2147483648, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellPriority': 50, 'SpellVisualID_1': 8529},
)


bad_attitude_50433 = spell(
    id=50433,
    name='Bad Attitude',
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=45000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=6, points_per_level=1.0379746835443038, die_sides=3, implicit_target_a=1, apply_aura=15),
    ],
    spell_icon_id=1581,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Snap back when struck.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Snap back for $s1 damage at any target that strikes you for the next $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellPriority': 50, 'SpellVisualID_1': 5287, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


nether_shock_50479 = spell(
    id=50479,
    name='Nether Shock',
    school=School.SHADOW,
    category=19,
    cast_time_ms=0,
    cooldown_ms=40000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=20.0,
    effects=[
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, mechanic=26, implicit_target_a=6, trigger_spell=62347),
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=3, points_per_level=0.759493670886076, die_sides=3, implicit_target_a=6),
    ],
    spell_icon_id=2027,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly lashes an enemy for $s2 Shadow damage.  Also interrupts spellcasting and prevents any spell in that school from being cast for $62347d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellVisualID_1': 4209},
)


savage_rend_50498 = spell(
    id=50498,
    name='Savage Rend',
    school=School.NORMAL,
    mechanic=15,
    attributes=16,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=20,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=4, points_per_level=0.6835443037974683, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, points_per_level=0.25316455696202533, mechanic=15, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=5000),
    ],
    spell_icon_id=245,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Physical damage inflicted every $t2 sec.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Slashes the enemy with the raptor's talons for $s1 damage, and causes the target to bleed for $s2 damage every $t2 sec for $d.  Successful critical strikes with this ability temporarily boost the raptor's damage by $50872s1% for $50872d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 100, 'ProcTypeMask': 16, 'RangeIndex': 2, 'SpellClassMask_2': 1342177280, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellVisualID_1': 372},
)


ravage_50518 = spell(
    id=50518,
    name='Ravage',
    school=School.NORMAL,
    mechanic=Mechanic.STUN,
    attributes=16,
    category=65,
    cast_time_ms=0,
    cooldown_ms=40000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=2000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=7, points_per_level=1.240506329113924, die_sides=3, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
    ],
    spell_icon_id=2253,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Stunned.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Violently attacks an enemy for $s1, stunning it for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellVisualID_1': 8102},
)


sonic_blast_50519 = spell(
    id=50519,
    name='Sonic Blast',
    school=School.NATURE,
    attributes=16,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=80,
    mana_cost_pct=0,
    range_yards=20.0,
    duration_ms=2000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=3, points_per_level=0.7341772151898734, die_sides=3, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, mechanic=Mechanic.STUN, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
    ],
    spell_icon_id=1577,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Stunned.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Emits a piercing shriek, inflicting $s1 Nature damage and stunning the target for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 25, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellPriority': 50, 'SpellVisualID_1': 7642},
)


snatch_50541 = spell(
    id=50541,
    name='Snatch',
    school=School.NORMAL,
    mechanic=3,
    attributes=16,
    category=109,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=60000,
    power_type=PowerType.FOCUS,
    mana_cost=20,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=6, points_per_level=1.0379746835443038, die_sides=3, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_DISARM),
    ],
    spell_icon_id=168,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134218240, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Disarmed!', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "The bird of prey grabs the enemy's weapon with its talons, causing $s1 damage and disarming them for $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellPriority': 50, 'SpellVisualID_1': 398},
)


master_s_call_53271 = spell(
    id=53271,
    name="Master's Call",
    school=School.NORMAL,
    attributes=16,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=25.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=54215, implicit_target_a=21),
        Effect(type=77, base_points=56650, implicit_target_a=5),
    ],
    spell_icon_id=3486,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 75, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your pet attempts to remove all root and movement impairing effects from itself and its target, and causes your pet and its target to be immune to all such effects for $54216d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 268435456, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassMask_3': 4, 'SpellClassSet': 9, 'SpellLevel': 75, 'SpellVisualID_1': 11997},
)


kill_shot_53351 = spell(
    id=53351,
    name='Kill Shot',
    school=School.NORMAL,
    attributes=4259858,
    category=1226,
    cooldown_ms=0,
    category_cooldown_ms=15000,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=45.0,
    effects=[
        Effect(type=17, base_points=204, points_per_level=13.333333333333334, implicit_target_a=6),
        Effect(type=31, base_points=199, implicit_target_a=6),
    ],
    spell_icon_id=3676,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 71); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 3 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 131072, 'AttributesEx4': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 71, 'CastingTimeIndex': 18, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You attempt to finish the wounded target off, firing a long range attack dealing $s2% weapon damage plus ${$RAP*0.40+$m1*2}. Kill Shot can only be used on enemies that have 20% or less health.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 262156, 'FacingCasterFlags': 1, 'InterruptFlags': 4, 'MaxLevel': 80, 'ModalNextSpell': 75, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 155, 'Speed': 40.0, 'SpellClassMask_2': 8388608, 'SpellClassSet': 9, 'SpellLevel': 71, 'SpellVisualID_1': 11780, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetAuraState': 2},
)


froststorm_breath_54644 = spell(
    id=54644,
    name='Froststorm Breath',
    school=School.NATURE | School.FROST,
    category=1247,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    power_type=PowerType.FOCUS,
    mana_cost=20,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=6, points_per_level=1.5316455696202531, die_sides=7, implicit_target_a=6, chain_targets=1),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=6, trigger_spell=54689),
        Effect(type=EffectType.APPLY_AURA, base_points=-51, mechanic=Mechanic.SNARE, implicit_target_a=6, apply_aura=AuraType.MOD_DECREASE_SPEED),
    ],
    spell_icon_id=62,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Slowed for $d.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your pet simultaneously breathes frost and lightning at an enemy target, inflicting $s1 Frost and Nature damage and slowing the target for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellVisualID_1': 4200},
)


monstrous_bite_54680 = spell(
    id=54680,
    name='Monstrous Bite',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=10000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=20,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=6, points_per_level=1.0632911392405062, die_sides=3, implicit_target_a=6),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, trigger_spell=54681),
    ],
    spell_icon_id=599,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your devilsaur ferociously bites the enemy, causing $s1 damage, and boosts its own damage by 3% for 12 seconds.  This effect stacks 3 times.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellVisualID_1': 376, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


venom_web_spray_54706 = spell(
    id=54706,
    name='Venom Web Spray',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    mechanic=Mechanic.ROOT,
    attributes=1073807360,
    cast_time_ms=0,
    cooldown_ms=40000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=4000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=AuraType.MOD_ROOT),
        Effect(type=EffectType.APPLY_AURA, points_per_level=0.569620253164557, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=1000),
    ],
    spell_icon_id=272,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Webbed and taking Nature damage over time.', 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Sprays toxic webs at the target, preventing movement for $d and causing Nature damage over time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellVisualID_1': 12013},
)


acid_spit_55749 = spell(
    id=55749,
    name='Acid Spit',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=10000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=20,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=7, points_per_level=1.4683544303797469, die_sides=5, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=6, apply_aura=101, misc_value=1),
    ],
    spell_icon_id=636,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Armor reduced by $s2%.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'CumulativeAura': 2, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your worm spits acid at an enemy, causing $s1 Nature damage and reducing its armor by $s2% per Acid Spit for $d.  Can be applied up to 2 times.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 24.0, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellPriority': 50, 'SpellVisualID_1': 854, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


sting_56626 = spell(
    id=56626,
    name='Sting',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=16,
    category=1133,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=6000,
    power_type=PowerType.FOCUS,
    mana_cost=20,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=3, points_per_level=0.759493670886076, die_sides=3, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=-6, implicit_target_a=6, apply_aura=101, misc_value=1),
    ],
    spell_icon_id=110,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 98816, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Decreases armor by $s2%.  Cannot stealth or turn invisible.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your wasp stings for $s1 Nature damage, and decreases the armor of the target by $s2% for $d.  While affected, the target cannot stealth or turn invisible.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 6, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellVisualID_1': 192, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


steady_shot_56641 = spell(
    id=56641,
    name='Steady Shot',
    school=School.NORMAL,
    attributes=4259858,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=35.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=44, points_per_level=6.9, implicit_target_a=6),
        Effect(type=EffectType.DUMMY, base_points=174),
    ],
    spell_icon_id=2228,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 50); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 4 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 131072, 'AttributesEx4': 134217728, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 50, 'CastingTimeIndex': 16, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A steady shot that causes unmodified weapon damage, plus ammo, plus ${$RAP*0.1+$m1}.  Causes an additional $s2 against Dazed targets.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 262156, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'ModalNextSpell': 75, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 114, 'Speed': 40.0, 'SpellClassMask_2': 1, 'SpellClassSet': 9, 'SpellLevel': 50, 'SpellVisualID_1': 8155, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


stampede_57386 = spell(
    id=57386,
    name='Stampede',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=60000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=13, points_per_level=2.1265822784810124, die_sides=5, implicit_target_a=6),
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=6, apply_aura=255, misc_value=15),
    ],
    spell_icon_id=3066,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'All bleed effects cause $s3% additional damage.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your rhino slams into a nearby enemy for $s1 damage, causing it to take $s3% additional damage from bleed effects for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMechanic_2': 6, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 53, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellVisualID_1': 9248},
)


lava_breath_58604 = spell(
    id=58604,
    name='Lava Breath',
    school=School.FIRE,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=10000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=20,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=6, points_per_level=1.5316455696202531, die_sides=7, implicit_target_a=6, chain_targets=1),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=6, trigger_spell=58605),
        Effect(type=EffectType.APPLY_AURA, base_points=-26, implicit_target_a=6, apply_aura=216),
    ],
    spell_icon_id=1197,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Casting speed slowed by $s3%.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your pet breathes a double gout of molten lava at the target for $s1 Fire damage and reduces the target's casting speed by $s3% for $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellVisualID_1': 8489, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


rake_59881 = spell(
    id=59881,
    name='Rake',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=10000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=20,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=9000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, points_per_level=0.5822784810126582, die_sides=3, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, points_per_level=0.22784810126582278, mechanic=15, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
    ],
    spell_icon_id=494,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 8, 'AttributesEx4': 1048576, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Bleeding for $s2 damage every $t2 seconds.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Rake the target for $s1 bleed damage and an additional $s2 damage every $t2 seconds.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'ImplicitTargetA_3': 6, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellVisualID_1': 750, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


freezing_arrow_60192 = spell(
    id=60192,
    name='Freezing Arrow',
    school=School.FROST,
    attributes=65536,
    category=411,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=30000,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=40.0,
    effects=[
        Effect(type=32, die_sides=0, implicit_target_a=87, trigger_spell=60202, radius_yards=2.0),
    ],
    spell_icon_id=189,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 134217728, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 80, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Fire a freezing arrow that places a Freezing Trap at the target location, freezing the first enemy that approaches, preventing all action for up to $14309d.  Any damage caused will break the ice.  Trap will exist for $60202d.  Only one trap can be active at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 262156, 'InterruptFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 45.0, 'SpellClassMask_1': 128, 'SpellClassSet': 9, 'SpellLevel': 80, 'SpellVisualID_1': 12409, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Targets': 64},
)


spirit_strike_61193 = spell(
    id=61193,
    name='Spirit Strike',
    school=School.ARCANE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=10000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=20,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=6, points_per_level=0.5316455696202531, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=6000),
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=6, points_per_level=0.5316455696202531, implicit_target_a=6),
    ],
    spell_icon_id=225,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s1 Arcane damage every $t1 seconds.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Burns the enemy for $s1 Arcane damage and then an additional $s1 after $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellPriority': 50, 'SpellVisualID_1': 1263, 'StartRecoveryTime': 1500},
)


aspect_of_the_dragonhawk_61846 = spell(
    id=61846,
    name='Aspect of the Dragonhawk',
    school=School.NATURE,
    attributes=327680,
    category=47,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=1000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=229, points_per_level=11.666666666666666, implicit_target_a=1, apply_aura=124),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=6150),
    ],
    spell_icon_id=2328,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 74); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 2 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'ActiveIconID': 122, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases ranged attack power by $s1.\r\nIncreases dodge chance by $61848s1%.', 'BaseLevel': 74, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The hunter takes on the aspects of a dragonhawk, increasing ranged attack power by $s1 and chance to dodge by $61848s1%.  Only one Aspect can be active at a time.', 'EffectBasePoints_3': 17, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassMask_3': 4096, 'SpellClassSet': 9, 'SpellLevel': 74, 'SpellVisualID_1': 3161},
)


call_stabled_pet_62757 = spell(
    id=62757,
    name='Call Stabled Pet',
    school=School.NORMAL,
    attributes=268501008,
    cast_time_ms=0,
    cooldown_ms=300000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=120000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=292),
    ],
    spell_icon_id=1522,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx4': 65536, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Choose one of your stabled pets to replace your current pet.', 'AuraInterruptFlags': 273158147, 'BaseLevel': 80, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Choose one of your stabled pets to replace your current pet.  The selected pet busts out of its stable to join you no matter where you are.  Cannot be used in combat.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ExcludeCasterAuraSpell': 61431, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_3': 1048576, 'SpellClassSet': 9, 'SpellLevel': 80, 'SpellPriority': 50, 'SpellVisualID_1': 3401, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


black_arrow_3674 = spell(
    id=3674,
    name='Black Arrow',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    attributes=65538,
    category=1250,
    cooldown_ms=0,
    category_cooldown_ms=30000,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=35.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=156, points_per_level=13.2, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=6, apply_aura=271),
    ],
    spell_icon_id=1939,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 50); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 131072, 'AttributesEx4': 2048, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'All damage taken increased by $s2%, and $s1 Shadow damage every $t1 seconds.', 'BaseLevel': 50, 'CastingTimeIndex': 18, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Fires a Black Arrow at the target, increasing all damage done by you to the target by $s2% and dealing ${$RAP*0.1+$m1*5} Shadow damage over $d. Black Arrow shares a cooldown with Trap spells.', 'EffectBasePoints_3': -1, 'EffectBonusMultiplier_2': 0.10000000149011612, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskB_1': 227329, 'EffectSpellClassMaskB_2': 2155872513, 'EffectSpellClassMaskB_3': 961, 'EquippedItemClass': 2, 'EquippedItemSubclass': 262156, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'ModalNextSpell': 75, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 114, 'Speed': 40.0, 'SpellClassMask_1': 128, 'SpellClassMask_2': 134217728, 'SpellClassSet': 9, 'SpellLevel': 50, 'SpellVisualID_1': 3222, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


counterattack_19306 = spell(
    id=19306,
    name='Counterattack',
    school=School.NORMAL,
    attributes=2424848,
    category=1135,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=5000,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=5.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=47, points_per_level=5.88, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, mechanic=Mechanic.ROOT, implicit_target_a=6, apply_aura=AuraType.MOD_ROOT),
    ],
    spell_icon_id=278,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 30); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AttributesEx4': 512, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Immobile.', 'BaseLevel': 30, 'CasterAuraState': 7, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "A strike that becomes active after parrying an opponent's attack.  This attack deals ${$AP*0.2+$m1} damage and immobilizes the target for $d.  Counterattack cannot be blocked, dodged, or parried.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 524288, 'SpellClassSet': 9, 'SpellLevel': 30, 'SpellVisualID_1': 5287, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


wyvern_sting_19386 = spell(
    id=19386,
    name='Wyvern Sting',
    school=School.NATURE,
    dispel=DispelType.POISON,
    mechanic=Mechanic.SLEEP,
    attributes=1114114,
    category=1111,
    cooldown_ms=0,
    category_cooldown_ms=60000,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=35.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, mechanic=Mechanic.SLEEP, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
    ],
    spell_icon_id=1721,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 40); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 131072, 'AttributesEx4': 8388608, 'AttributesEx5': 32, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Asleep.', 'AuraInterruptFlags': 4718594, 'BaseLevel': 40, 'CastingTimeIndex': 18, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A stinging shot that puts the target to sleep for $d.  Any damage will cancel the effect.  When the target wakes up, the Sting causes $24131o1 Nature damage over $24131d.  Only one Sting per Hunter can be active on the target at a time.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': 2, 'EquippedItemSubclass': 262156, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 100, 'ProcTypeMask': 1048576, 'RangeIndex': 114, 'Speed': 40.0, 'SpellClassMask_2': 4096, 'SpellClassSet': 9, 'SpellLevel': 40, 'SpellVisualID_1': 7205, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


aimed_shot_19434 = spell(
    id=19434,
    name='Aimed Shot',
    school=School.NORMAL,
    attributes=65554,
    category=85,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=35.0,
    duration_ms=10000,
    effects=[
        Effect(type=121, base_points=4, points_per_level=6.716666666666667, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=6, apply_aura=AuraType.MOD_HEALING_PCT, misc_value=127),
    ],
    spell_icon_id=1629,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 131072, 'AttributesEx4': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Healing effects reduced by $s2%.', 'BaseLevel': 20, 'CastingTimeIndex': 18, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'An aimed shot that increases ranged damage by $s1 and reduces healing done to that target by $s2%.  Lasts $d.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 262156, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'ModalNextSpell': 75, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 114, 'Speed': 40.0, 'SpellClassMask_1': 131072, 'SpellClassSet': 9, 'SpellLevel': 20, 'SpellVisualID_1': 7955, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


explosive_shot_53301 = spell(
    id=53301,
    name='Explosive Shot',
    school=School.FIRE,
    attributes=67586,
    category=1173,
    cooldown_ms=0,
    category_cooldown_ms=6000,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=35.0,
    duration_ms=2000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=143, points_per_level=12.1, die_sides=29, implicit_target_a=6, apply_aura=226, amplitude=1000),
    ],
    spell_icon_id=3407,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 60); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 4 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 131072, 'AttributesEx5': 512, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Taking Fire damage every second.', 'BaseLevel': 60, 'CastingTimeIndex': 18, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You fire an explosive charge into the enemy target, dealing ${$RAP*0.14+$m1}-${$RAP*0.14+$M1} Fire damage. The charge will blast the target every second for an additional $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 262156, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'ModalNextSpell': 75, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 114, 'Speed': 40.0, 'SpellClassMask_2': 2147483648, 'SpellClassSet': 9, 'SpellLevel': 60, 'SpellVisualID_1': 11828, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


scatter_shot_19503 = spell(
    id=19503,
    name='Scatter Shot',
    school=School.NORMAL,
    attributes=1114114,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=15.0,
    duration_ms=4000,
    effects=[
        Effect(type=31, base_points=49, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, mechanic=Mechanic.DISORIENTED, implicit_target_a=6, apply_aura=AuraType.MOD_CONFUSE),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=6, trigger_spell=37506),
    ],
    spell_icon_id=132,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 131072, 'AttributesEx4': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Disoriented.', 'AuraInterruptFlags': 4718594, 'BaseLevel': 15, 'CastingTimeIndex': 18, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A short-range shot that deals $s1% weapon damage and disorients the target for $d.  Any damage caused will remove the effect.  Turns off your attack when used.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 262156, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'Speed': 60.0, 'SpellClassMask_1': 262144, 'SpellClassMask_3': 32768, 'SpellClassSet': 9, 'SpellLevel': 15, 'SpellVisualID_1': 8346, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


bestial_wrath_19574 = spell(
    id=19574,
    name='Bestial Wrath',
    school=School.NORMAL,
    attributes=536936448,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=100.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=5, apply_aura=61),
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=5, apply_aura=79, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=5, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=12),
    ],
    spell_icon_id=1680,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 33792, 'AttributesEx5': 393224, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Enraged.', 'BaseLevel': 40, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Send your pet into a rage causing $s2% additional damage for $d.  While enraged, the beast does not feel pity or remorse or fear and it cannot be stopped unless killed.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassMask_2': 33554432, 'SpellClassSet': 9, 'SpellLevel': 40, 'SpellVisualID_1': 7278, 'TargetCreatureType': 1},
)


intimidation_19577 = spell(
    id=19577,
    name='Intimidation',
    school=School.NATURE,
    attributes=329744,
    category=1132,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=100.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=5, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=24394),
        Effect(type=77, die_sides=0, implicit_target_a=5),
    ],
    spell_icon_id=166,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 4, 'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Stuns the target for $24394d.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Command your pet to intimidate the target, causing a high amount of threat and stunning the target for $24394d. Lasts $19577d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 20, 'SpellClassMask_3': 8, 'SpellClassSet': 9, 'SpellLevel': 30, 'SpellVisualID_1': 9178, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetCreatureType': 1},
)


dive_23145 = spell(
    id=23145,
    name='Dive',
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=32000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=30,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=16000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=79, implicit_target_a=1, apply_aura=AuraType.MOD_INCREASE_SPEED),
    ],
    spell_icon_id=208,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases movement speed by $s1%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your pet's movement speed by $s1% for $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 805306368, 'SpellClassSet': 9, 'SpellVisualID_1': 2276},
)


readiness_23989 = spell(
    id=23989,
    name='Readiness',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=2238,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 32, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When activated, this ability immediately finishes the cooldown on your other Hunter abilities except Bestial Wrath.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9, 'SpellVisualID_1': 8345, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


silencing_shot_34490 = spell(
    id=34490,
    name='Silencing Shot',
    school=School.NORMAL,
    dispel=DispelType.MAGIC,
    attributes=65538,
    cooldown_ms=20000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=35.0,
    duration_ms=3000,
    effects=[
        Effect(type=31, base_points=49, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, mechanic=Mechanic.SILENCE, implicit_target_a=6, apply_aura=AuraType.MOD_SILENCE),
    ],
    spell_icon_id=127,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 131072, 'AttributesEx7': 2048, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Silenced.', 'BaseLevel': 30, 'CastingTimeIndex': 18, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A shot that deals $s1% weapon damage and Silences the target for $d.  Non-player victim spellcasting is also interrupted for $32747d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMechanic_3': 26, 'EquippedItemClass': 2, 'EquippedItemSubclass': 262156, 'FacingCasterFlags': 1, 'ModalNextSpell': 75, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 114, 'Speed': 60.0, 'SpellClassMask_1': 262144, 'SpellClassSet': 9, 'SpellLevel': 30, 'SpellVisualID_1': 8344},
)


swoop_52825 = spell(
    id=52825,
    name='Swoop',
    school=School.NORMAL,
    attributes=537198608,
    cast_time_ms=0,
    cooldown_ms=25000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=35,
    mana_cost_pct=0,
    range_yards=25.0,
    duration_ms=4000,
    effects=[
        Effect(type=96, die_sides=0, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=166),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=1, trigger_spell=53148),
    ],
    spell_icon_id=2328,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx7': 262144, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your pet swoops at an enemy, immobilizing the target for $53148d, and adds $52825s2% melee attack power to the pet's next attack.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ExcludeTargetAuraSpell': 65219, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'ProcCharges': 1, 'ProcTypeMask': 20, 'RangeIndex': 95, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellVisualID_1': 1104, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


chimera_shot_53209 = spell(
    id=53209,
    name='Chimera Shot',
    school=School.NATURE,
    attributes=65538,
    cooldown_ms=10000,
    category_cooldown_ms=6000,
    mana_cost=0,
    mana_cost_pct=12,
    range_yards=35.0,
    effects=[
        Effect(type=77, die_sides=0, implicit_target_a=6),
        Effect(type=121, base_points=-1, implicit_target_a=6),
        Effect(type=31, base_points=124, implicit_target_a=6),
    ],
    spell_icon_id=3412,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 131072, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 18, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You deal $s3% weapon damage, refreshing the current Sting on your target and triggering an effect:\r\n\r\nSerpent Sting - Instantly deals 40% of the damage done by your Serpent Sting.\r\n\r\nViper Sting - Instantly restores mana to you equal to 60% of the total amount drained by your Viper Sting.\r\n\r\nScorpid Sting - Attempts to Disarm the target for 10 sec. This effect cannot occur more than once per 1 minute.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 262156, 'FacingCasterFlags': 1, 'ModalNextSpell': 75, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 114, 'Speed': 40.0, 'SpellClassMask_3': 1, 'SpellClassSet': 9, 'SpellLevel': 60, 'SpellVisualID_1': 11725, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


rabid_53401 = spell(
    id=53401,
    name='Rabid',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=45000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=53403),
    ],
    spell_icon_id=2852,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': "Hits can increase the pet's attack power.", 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your pet goes into a killing frenzy.  Successful attacks have a chance to increase attack power by $53403s1%.  This effect will stack up to $53403u times.  Lasts $53401d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'ProcTypeMask': 4, 'RangeIndex': 1, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellVisualID_1': 8338},
)


lick_your_wounds_53426 = spell(
    id=53426,
    name='Lick Your Wounds',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=20, amplitude=1000),
    ],
    spell_icon_id=267,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 64, 'AttributesEx5': 8192, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Gain $s1% of total health every $t1 sec.', 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31756, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your pet heals itself for $o1% of its total health over $d while channeling.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellPriority': 50, 'SpellVisualID_1': 12983},
)


call_of_the_wild_53434 = spell(
    id=53434,
    name='Call of the Wild',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=300000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=20, apply_aura=166, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=20, apply_aura=167, radius_yards=100.0),
    ],
    spell_icon_id=2850,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 4, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases your melee and ranged attack power by $s1%.', 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your pet roars, increasing your pet's and your melee and ranged attack power by $s1%.  Lasts $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellPriority': 50, 'SpellVisualID_1': 246},
)


intervene_53476 = spell(
    id=53476,
    name='Intervene',
    school=School.NORMAL,
    attributes=536870928,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=20,
    mana_cost_pct=0,
    range_yards=25.0,
    duration_ms=10000,
    effects=[
        Effect(type=96, base_points=-1, implicit_target_a=57),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=57, apply_aura=111, radius_yards=10.0),
    ],
    spell_icon_id=1588,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx5': 2048, 'AttributesEx7': 262144, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'The next melee or ranged attack made against you will be made against the intervening pet instead.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your pet runs at high speed towards a group member, intercepting the next melee or ranged attack made against them.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ExcludeTargetAuraSpell': 65219, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 680, 'RangeIndex': 95, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellVisualID_1': 9107},
)


taunt_53477 = spell(
    id=53477,
    name='Taunt',
    school=School.NORMAL,
    mechanic=16,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=3000,
    effects=[
        Effect(type=114, die_sides=0, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=AuraType.MOD_TAUNT),
    ],
    spell_icon_id=24,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 67108864, 'AttributesEx4': 2048, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Taunted.', 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your pet taunts the target to attack it for $d.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellVisualID_1': 34},
)


last_stand_53478 = spell(
    id=53478,
    name='Last Stand',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=360000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=2024,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your pet temporarily gains 30% of its maximum health for $53479d.  After the effect expires, the health is lost.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellPriority': 50},
)


roar_of_sacrifice_53480 = spell(
    id=53480,
    name='Roar of Sacrifice',
    school=School.NATURE,
    attributes=16,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=40.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-10001, implicit_target_a=21, apply_aura=197, misc_value=127),
    ],
    spell_icon_id=960,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 524288, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': "Immune to critical strikes, but damage transferred to the hunter's pet.", 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Protects a friendly target from critical strikes, making attacks against that target unable to be critical strikes, but $s2% of all damage taken by that target is also taken by the pet.  Lasts $d.', 'EffectBasePoints_2': 19, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 20, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 664232, 'SpellClassMask_1': 65536, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellPriority': 50, 'SpellVisualID_1': 246},
)


bullheaded_53490 = spell(
    id=53490,
    name='Bullheaded',
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=100,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=1),
        Effect(type=EffectType.TRIGGER_SPELL, base_points=-1, trigger_spell=63896),
    ],
    spell_icon_id=2769,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 32768, 'AttributesEx5': 393224, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Removes all movement impairing effects and all effects which cause loss of control of your pet, and reduces damage done to your pet by $63896s1% for $63896d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellVisualID_1': 86, 'StartRecoveryTime': 1500},
)


wolverine_bite_53508 = spell(
    id=53508,
    name='Wolverine Bite',
    school=School.NORMAL,
    attributes=2097168,
    category=65,
    cast_time_ms=0,
    cooldown_ms=10000,
    category_cooldown_ms=5000,
    power_type=PowerType.FOCUS,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=4, points_per_level=5.0, implicit_target_a=6),
    ],
    spell_icon_id=2246,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 135266816, 'AttributesEx4': 512, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A fierce attack causing $s1 damage, modified by pet level, that your pet can use after it makes a critical attack.  Cannot be dodged, blocked or parried.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'RangeIndex': 2, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellVisualID_1': 39, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


roar_of_recovery_53517 = spell(
    id=53517,
    name='Roar of Recovery',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=40.0,
    duration_ms=9000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=27, apply_aura=21, amplitude=3000),
    ],
    spell_icon_id=2851,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Gain $s1% of total mana every $t1 sec.', 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your pet's inspiring roar restores $o1% of your total mana over $d.", 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 27, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 268439552, 'SpellClassSet': 9, 'SpellVisualID_1': 246},
)


carrion_feeder_54044 = spell(
    id=54044,
    name='Carrion Feeder',
    school=School.NORMAL,
    attributes=16,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.DUMMY, die_sides=0, radius_yards=5.0),
    ],
    spell_icon_id=146,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 1, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your pet can generate health and happiness by eating a corpse.  Will not work on the remains of elemental or mechanical creatures.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 2, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'TargetCreatureType': 119},
)


heart_of_the_phoenix_55709 = spell(
    id=55709,
    name='Heart of the Phoenix',
    school=School.NATURE,
    attributes=8388608,
    category=1156,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=480000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=77, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=2787,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 1, 'AttributesEx3': 1048576, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When your pet dies, it will miraculously return to life with full health.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 9, 'StartRecoveryCategory': 1156},
)


dash_61684 = spell(
    id=61684,
    name='Dash',
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=32000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=30,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=16000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=79, implicit_target_a=1, apply_aura=AuraType.MOD_INCREASE_SPEED),
    ],
    spell_icon_id=959,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 32, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases movement speed by $s1%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your pet's movement speed by $s1% for $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 805306368, 'SpellClassSet': 9, 'SpellVisualID_1': 2276},
)


charge_61685 = spell(
    id=61685,
    name='Charge',
    school=School.NORMAL,
    attributes=537198608,
    cast_time_ms=0,
    cooldown_ms=25000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=35,
    mana_cost_pct=0,
    range_yards=25.0,
    duration_ms=4000,
    effects=[
        Effect(type=96, die_sides=0, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=166),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=6, trigger_spell=53148),
    ],
    spell_icon_id=1559,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx7': 262144, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Attack power increased by $61685s2%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your pet charges an enemy, immobilizing the target for $53148d, and increasing the pet's melee attack power by $61685s2% for its next attack.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'ProcCharges': 1, 'ProcTypeMask': 20, 'RangeIndex': 95, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellVisualID_1': 519, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


thunderstomp_63900 = spell(
    id=63900,
    name='Thunderstomp',
    school=School.NATURE,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=10000,
    category_cooldown_ms=0,
    power_type=PowerType.FOCUS,
    mana_cost=20,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=2, points_per_level=2.0, die_sides=3, implicit_target_a=53, implicit_target_b=16, radius_yards=8.0),
    ],
    spell_icon_id=148,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 640, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shakes the ground with thundering force, doing $s1 Nature damage to all enemies within $a1 yards.  This ability causes a moderate amount of additional threat.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'RangeIndex': 2, 'SpellClassMask_2': 268435456, 'SpellClassSet': 9, 'SpellLevel': 1, 'SpellVisualID_1': 7429, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
