"""
Deathknight - player-castable spells (real cast_time_ms/cooldown_ms, not marked passive).

Split from a single source/classes/deathknight.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .deathknight_...` below) resolve.
"""

from lib.dsl import AuraType, DispelType, Effect, EffectType, Mechanic, PowerType, School
from lib.dsl.registry import spell


army_of_the_dead_42650 = spell(
    id=42650,
    name='Army of the Dead',
    school=School.SHADOW,
    cast_time_ms=0,
    cooldown_ms=600000,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=4000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=500, trigger_spell=42651),
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        Effect(type=77, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=2718,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 132160, 'AttributesEx4': 65536, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Summoning Ghouls.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 15372, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons an entire legion of Ghouls to fight for the Death Knight.  The Ghouls will swarm the area, taunting and fighting anything they can.  While channelling Army of the Dead, the Death Knight takes less damage equal to $Ghis:her; Dodge plus Parry chance.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 81, 'SpellClassMask_1': 2048, 'SpellClassSet': 15, 'SpellLevel': 60, 'SpellVisualID_1': 9607, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


death_and_decay_43265 = spell(
    id=43265,
    name='Death and Decay',
    school=School.SHADOW,
    attributes=67108864,
    category=18,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=30000,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.PERSISTENT_AREA_AURA, base_points=25, points_per_level=1.8, implicit_target_a=28, apply_aura=226, amplitude=1000, radius_yards=10.0),
    ],
    spell_icon_id=118,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 60); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 4 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 136, 'AttributesEx5': 512, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s1 Shadow damage inflicted every sec.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Corrupts the ground targeted by the Death Knight, causing $m1 Shadow damage every sec that targets remain in the area for $d.  This ability produces a high amount of threat.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RuneCostID': 101, 'SpellClassMask_1': 32, 'SpellClassSet': 15, 'SpellLevel': 30, 'SpellVisualID_1': 9735, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Targets': 64},
)


blood_tap_45529 = spell(
    id=45529,
    name='Blood Tap',
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    power_type=PowerType.HEALTH,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=0.0,
    duration_ms=20000,
    effects=[
        Effect(type=146, implicit_target_a=1, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=249),
        Effect(type=EffectType.ENERGIZE, base_points=99, implicit_target_a=1, misc_value=6),
    ],
    spell_icon_id=2724,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx2': 33554432, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Blood Rune converted to a Death Rune.', 'BaseLevel': 26, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Immediately activates a Blood Rune and converts it into a Death Rune for the next $d.  Death Runes count as a Blood, Frost or Unholy Rune.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_2': 3, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 262, 'SpellClassMask_1': 8, 'SpellClassSet': 15, 'SpellLevel': 26, 'SpellVisualID_1': 11149},
)


raise_dead_46584 = spell(
    id=46584,
    name='Raise Dead',
    school=School.NORMAL,
    attributes=2181038080,
    category=1245,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=180000,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    effects=[
        None,
        Effect(type=77, base_points=46584, implicit_target_a=18, implicit_target_b=8, radius_yards=30.0),
        Effect(type=EffectType.DUMMY, base_points=52149, implicit_target_a=1),
    ],
    spell_icon_id=221,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 132096, 'AttributesEx2': 1, 'AttributesEx3': 262144, 'AttributesEx5': 2097152, 'AttributesEx6': 32, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'A Risen Ghoul is in your service.', 'BaseLevel': 12, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Raises a Ghoul to fight by your side.  If no humanoid corpse that yields experience or honor is available, you must supply Corpse Dust to complete the spell.  You can have a maximum of one Ghoul at a time.  Lasts $46585d.', 'EffectBasePoints_1': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_1': 1, 'EquippedItemClass': -1, 'ImplicitTargetA_1': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RuneCostID': 341, 'SpellClassMask_1': 4096, 'SpellClassSet': 15, 'SpellLevel': 12, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


strangulate_47476 = spell(
    id=47476,
    name='Strangulate',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    mechanic=Mechanic.SILENCE,
    attributes=262144,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, mechanic=Mechanic.SILENCE, implicit_target_a=6, apply_aura=AuraType.MOD_SILENCE),
        None,
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2027,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 134217728, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Silenced.', 'BaseLevel': 28, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Strangulates an enemy, silencing them for $d.  Non-player victim spellcasting is also interrupted for $32747d.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'ImplicitTargetA_2': 6, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RuneCostID': 401, 'SpellClassMask_1': 512, 'SpellClassSet': 15, 'SpellLevel': 28, 'SpellVisualID_1': 11154, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


mind_freeze_47528 = spell(
    id=47528,
    name='Mind Freeze',
    school=School.FROST,
    category=88,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    power_type=PowerType.RUNIC_POWER,
    mana_cost=200,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=4000,
    effects=[
        Effect(type=EffectType.INTERRUPT_CAST, base_points=-1, mechanic=26, implicit_target_a=6),
    ],
    spell_icon_id=2722,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 512, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 18, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Smash the target's mind with cold, interrupting spellcasting and preventing any spell in that school from being cast for $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'ImplicitTargetA_2': 6, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 2, 'RuneCostID': 421, 'SpellClassMask_1': 1024, 'SpellClassSet': 15, 'SpellLevel': 18, 'SpellVisualID_1': 11153},
)


death_coil_47541 = spell(
    id=47541,
    name='Death Coil',
    school=School.SHADOW,
    attributes=262144,
    category=633,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNIC_POWER,
    mana_cost=400,
    mana_cost_pct=0,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=166, points_per_level=11.04, implicit_target_a=25),
    ],
    spell_icon_id=88,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 55); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 1024, 'AuraDescription_Lang_Mask': 16712174, 'BaseLevel': 4, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Fire a blast of unholy energy, causing $<damage> Shadow damage to an enemy target or healing $<healing> damage from a friendly Undead target$?s58677[.  Refunds $58677s1 runic power when used to heal.][.]', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 160, 'RuneCostID': 422, 'SpellClassMask_1': 8192, 'SpellClassSet': 15, 'SpellDescriptionVariableID': 84, 'SpellLevel': 4, 'SpellPriority': 50, 'SpellVisualID_1': 10755, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


empower_rune_weapon_47568 = spell(
    id=47568,
    name='Empower Rune Weapon',
    attributes=262144,
    cast_time_ms=0,
    cooldown_ms=300000,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=146, base_points=1, implicit_target_a=1),
        Effect(type=146, base_points=1, implicit_target_a=1, misc_value=1),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=1, trigger_spell=53258),
    ],
    spell_icon_id=2622,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 1024, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 54, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Empower your rune weapon, immediately activating all your runes and generating 25 runic power.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 1144, 'Speed': 1.0, 'SpellClassMask_1': 16384, 'SpellClassSet': 15, 'SpellLevel': 54, 'SpellVisualID_1': 10590},
)


frost_presence_48263 = spell(
    id=48263,
    name='Frost Presence',
    school=School.FROST,
    attributes=2835677200,
    category=47,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=1000,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=59, implicit_target_a=1, apply_aura=142, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=44, implicit_target_a=1, apply_aura=AuraType.MOD_THREAT, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=-9, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
    ],
    spell_icon_id=2632,
    notes='pulled from existing data',
    raw_overrides={'ActiveIconID': 2632, 'AttributesEx': 1024, 'AttributesEx2': 17, 'AttributesEx3': 1114112, 'AttributesEx4': 2097152, 'AttributesEx6': 4096, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Stamina increased by $61261s1%.\r\nArmor contribution from cloth, leather, mail and plate items increased by $48263s1%.\r\nDamage taken reduced by $48263s3%.', 'BaseLevel': 10, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The death knight takes on the presence of frost, increasing Stamina by $61261s1%, armor contribution from cloth, leather, mail and plate items by $48263s1%, and reducing damage taken by $48263s3%.  Increases threat generated.  Only one Presence may be active at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 482, 'SpellClassMask_1': 32768, 'SpellClassSet': 15, 'SpellLevel': 10, 'SpellVisualID_1': 11115, 'StanceBarOrder': 1},
)


unholy_presence_48265 = spell(
    id=48265,
    name='Unholy Presence',
    school=School.SHADOW,
    attributes=2835677200,
    category=47,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=1000,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=138),
        Effect(type=EffectType.APPLY_AURA, base_points=-501, implicit_target_a=1, apply_aura=107, misc_value=21),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=AuraType.MOD_THREAT, misc_value=127),
    ],
    spell_icon_id=2633,
    notes='pulled from existing data',
    raw_overrides={'ActiveIconID': 2633, 'AttributesEx': 1024, 'AttributesEx2': 17, 'AttributesEx3': 1114112, 'AttributesEx4': 2097152, 'AttributesEx6': 4096, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Attack speed increased $s1%.\r\nMovement speed increased by $49772s1%.\r\nGlobal cooldown on all abilities reduced by ${$m2/-1000}.1 sec.', 'BaseLevel': 40, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Infuses the death knight with unholy fury, increasing attack speed by $s1%, movement speed by $49772s1% and reducing the global cooldown on all abilities by ${$m2/-1000}.1 sec.  Only one Presence may be active at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 4292869759, 'EffectSpellClassMaskB_2': 1208685047, 'EffectSpellClassMaskB_3': 32, 'EffectSpellClassMaskC_1': 4227858431, 'EffectSpellClassMaskC_2': 511, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 483, 'SpellClassMask_1': 65536, 'SpellClassSet': 15, 'SpellLevel': 40, 'SpellVisualID_1': 11116, 'StanceBarOrder': 2},
)


anti_magic_shell_48707 = spell(
    id=48707,
    name='Anti-Magic Shell',
    school=School.SHADOW,
    attributes=262144,
    cast_time_ms=0,
    cooldown_ms=45000,
    category_cooldown_ms=45000,
    power_type=PowerType.RUNIC_POWER,
    mana_cost=200,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=74, mechanic=26, implicit_target_a=1, apply_aura=69, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=267, misc_value=126),
    ],
    spell_icon_id=99,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx4': 64, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Spell damage reduced by $s1%.\r\nImmune to magic debuffs.', 'BaseLevel': 46, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Surrounds the Death Knight in an Anti-Magic Shell, absorbing $48707s1% of the damage dealt by harmful spells (up to a maximum of $s2% of the Death Knight's health) and preventing application of harmful magical effects.  Damage absorbed by Anti-Magic Shell energizes the Death Knight with additional runic power.  Lasts $48707d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 522, 'SpellClassMask_1': 131072, 'SpellClassSet': 15, 'SpellLevel': 46, 'SpellVisualID_1': 11869},
)


death_pact_48743 = spell(
    id=48743,
    name='Death Pact',
    school=School.SHADOW,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    power_type=PowerType.RUNIC_POWER,
    mana_cost=400,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=1),
        Effect(type=1, base_points=-1, implicit_target_a=18, implicit_target_b=31, radius_yards=100.0),
        Effect(type=EffectType.HEAL, base_points=39, implicit_target_a=1),
    ],
    spell_icon_id=169,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 656384, 'AttributesEx2': 536870916, 'AttributesEx3': 1048576, 'AttributesEx4': 16, 'AttributesEx5': 2097152, 'AuraDescription_Lang_Mask': 16712172, 'BaseLevel': 38, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Sacrifices an undead minion, healing the Death Knight for $s3% of $Ghis:her; maximum health.  This heal cannot be a critical.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 541, 'SpellClassMask_1': 524288, 'SpellClassSet': 15, 'SpellLevel': 38, 'SpellVisualID_1': 11150, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


icebound_fortitude_48792 = spell(
    id=48792,
    name='Icebound Fortitude',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    power_type=PowerType.RUNIC_POWER,
    mana_cost=200,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
    ],
    spell_icon_id=2720,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage taken reduced.\r\nImmune to Stun effects.', 'BaseLevel': 40, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The Death Knight freezes $Ghis:her; blood to become immune to Stun effects and reduce all damage taken by $?s58625[$58625s1][$s3]% plus additional damage reduction based on Defense for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'RangeIndex': 1, 'RuneCostID': 561, 'SpellClassMask_1': 1048576, 'SpellClassSet': 15, 'SpellLevel': 40, 'SpellVisualID_1': 11151},
)


dark_command_56222 = spell(
    id=56222,
    name='Dark Command',
    school=School.NORMAL,
    attributes=327696,
    category=82,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=8000,
    power_type=PowerType.RAGE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=3000,
    effects=[
        Effect(type=114, die_sides=0, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=AuraType.MOD_TAUNT),
    ],
    spell_icon_id=2024,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 67108864, 'AttributesEx4': 2048, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Taunted.', 'BaseLevel': 10, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Commands the target to attack you, but has no effect if the target is already attacking you.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 268435456, 'SpellClassSet': 15, 'SpellLevel': 10, 'SpellVisualID_1': 34},
)


rune_strike_56815 = spell(
    id=56815,
    name='Rune Strike',
    school=School.NORMAL,
    attributes=2359316,
    category=65,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNIC_POWER,
    mana_cost=200,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.WEAPON_DAMAGE, base_points=-1, implicit_target_a=6),
        Effect(type=31, base_points=149, implicit_target_a=6),
    ],
    spell_icon_id=3007,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AttributesEx4': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 14, 'CasterAuraSpell': 56817, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Strike the target for $s2% weapon damage plus ${$m2*$AP*$m3/10000}.  Only usable after the Death Knight dodges or parries.  Can't be dodged, blocked, or parried.  This attack causes a high amount of threat.", 'EffectBasePoints_3': 9, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'RangeIndex': 2, 'SpellClassMask_2': 536870912, 'SpellClassSet': 15, 'SpellLevel': 14, 'SpellVisualID_1': 39},
)


horn_of_winter_57330 = spell(
    id=57330,
    name='Horn of Winter',
    school=School.NORMAL,
    attributes=327696,
    category=1253,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=20000,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=120000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=85, points_per_level=4.6, implicit_target_a=56, apply_aura=AuraType.MOD_STAT, radius_yards=30.0),
        Effect(type=EffectType.APPLY_AURA, base_points=85, points_per_level=4.6, implicit_target_a=1, implicit_target_b=56, apply_aura=AuraType.MOD_STAT, misc_value=1, radius_yards=30.0),
    ],
    spell_icon_id=2494,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 65); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 2 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases your total Strength and Agility by $s1.', 'BaseLevel': 8, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The Death Knight blows the Horn of Winter, which generates 10 runic power and increases total Strength and Agility of all party or raid members within $a1 yards by $s1.  Lasts $d.', 'EffectBasePoints_3': 44, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 1704, 'SpellClassMask_2': 1073741824, 'SpellClassSet': 15, 'SpellLevel': 8, 'SpellPriority': 50, 'SpellVisualID_1': 12396, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


raise_ally_61999 = spell(
    id=61999,
    name='Raise Ally',
    school=School.NORMAL,
    attributes=2147483648,
    cast_time_ms=0,
    cooldown_ms=600000,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=46618, implicit_target_a=57),
        Effect(type=77, die_sides=0, implicit_target_a=18, implicit_target_b=8, radius_yards=100.0),
    ],
    spell_icon_id=1591,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 1, 'AttributesEx3': 262400, 'AttributesEx4': 65536, 'AttributesEx5': 2097152, 'AttributesEx6': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 50, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Raises the corpse of a raid or party member to fight by your side.  The player will have control over the Ghoul for $46619d.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RuneCostID': 1684, 'SpellClassMask_2': 2147483648, 'SpellClassSet': 15, 'SpellLevel': 50, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


frost_strike_49143 = spell(
    id=49143,
    name='Frost Strike',
    school=School.FROST,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNIC_POWER,
    mana_cost=400,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=121, base_points=86, points_per_level=6.52, implicit_target_a=6),
        Effect(type=31, base_points=54, implicit_target_a=6),
    ],
    spell_icon_id=2740,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 55); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly strike the enemy, causing $s2% weapon damage plus ${$m1*$m2/100} as Frost damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskC_2': 4, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'RuneCostID': 621, 'SpellClassMask_2': 4, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellVisualID_1': 11612, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


corpse_explosion_49158 = spell(
    id=49158,
    name='Corpse Explosion',
    school=School.SHADOW,
    category=1240,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=5000,
    power_type=PowerType.RUNIC_POWER,
    mana_cost=400,
    mana_cost_pct=0,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=165, points_per_level=11.08, implicit_target_a=25),
        Effect(type=EffectType.DUMMY, base_points=50443, implicit_target_a=63, implicit_target_b=8, radius_yards=10.0),
    ],
    spell_icon_id=1737,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 55); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 1, 'AttributesEx5': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Cause a corpse to explode for $s1 Shadow damage to all enemies within $50444A1 yards.  Will use a nearby corpse if the target is not a corpse.  Does not affect mechanical or elemental corpses.', 'EffectBonusMultiplier_3': 0.0, 'EffectChainAmplitude_1': 3.5999999046325684, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 33554432, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RuneCostID': 1182, 'SpellClassSet': 15, 'SpellLevel': 55, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetCreatureType': 895},
)


howling_blast_49184 = spell(
    id=49184,
    name='Howling Blast',
    school=School.FROST,
    category=1248,
    cast_time_ms=0,
    cooldown_ms=8000,
    category_cooldown_ms=8000,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=20.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=149, implicit_target_a=6),
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=197, points_per_level=12.8, die_sides=17, implicit_target_a=53, implicit_target_b=16, radius_yards=10.0),
    ],
    spell_icon_id=2131,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 55); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 4 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134217864, 'AttributesEx6': 1024, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Blast the target with a frigid wind dealing $s2 Frost damage to all enemies within 10 yards.', 'EffectBasePoints_3': 49, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 14684919, 'EffectSpellClassMaskB_1': 12589815, 'EffectSpellClassMaskC_1': 4194437, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RuneCostID': 647, 'SpellClassMask_2': 2, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50, 'SpellVisualID_1': 11617, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


rune_tap_48982 = spell(
    id=48982,
    name='Rune Tap',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=136, base_points=9, implicit_target_a=1),
    ],
    spell_icon_id=2726,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 570425344, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Converts 1 Blood Rune into $s1% of your maximum health.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 581, 'SpellClassMask_1': 134217728, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellVisualID_1': 11512},
)


mark_of_blood_49005 = spell(
    id=49005,
    name='Mark of Blood',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    attributes=67371008,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=6, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2285,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 134218752, 'AttributesEx3': 67305473, 'AttributesEx4': 1572864, 'AttributesEx5': 32, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Hits by this target restore $s2% health.', 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Place a Mark of Blood on an enemy.  Whenever the marked enemy deals damage to a target, that target is healed for $49005s2% of its maximum health.  Lasts for $49005d or up to $49005n hits.', 'EffectBasePoints_2': 3, 'EffectBasePoints_3': 299, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcCharges': 20, 'ProcTypeMask': 332116, 'RuneCostID': 583, 'SpellClassMask_1': 268435456, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50, 'SpellVisualID_1': 11513, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


hysteria_49016 = spell(
    id=49016,
    name='Hysteria',
    school=School.NORMAL,
    dispel=9,
    mechanic=31,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=57, apply_aura=79, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=57, apply_aura=226, amplitude=1000, misc_value=126),
    ],
    spell_icon_id=2731,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx3': 131072, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Enraged.\r\nPhysical damage increased by $s1%.\r\nHealth equal to $s2% of maximum health lost every sec.', 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Induces a friendly unit into a killing frenzy for $d.  The target is Enraged, which increases their physical damage by $s1%, but causes them to lose health equal to $s2% of their maximum health every second.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RuneCostID': 643, 'SpellClassMask_1': 536870912, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellVisualID_1': 11514},
)


dancing_rune_weapon_49028 = spell(
    id=49028,
    name='Dancing Rune Weapon',
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=90000,
    category_cooldown_ms=0,
    power_type=PowerType.RUNIC_POWER,
    mana_cost=600,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.SUMMON, implicit_target_a=64, misc_value=27893, radius_yards=2.0),
        Effect(type=EffectType.APPLY_AURA, base_points=50706, implicit_target_a=1, apply_aura=AuraType.DUMMY, trigger_spell=1206),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=6, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2657,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67109890, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'You have recently summoned a rune weapon.', 'BaseLevel': 55, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a second rune weapon that fights on its own for $d, doing the same attacks as the Death Knight but for $51906s3% reduced damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 208, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 86288, 'SpellClassMask_1': 1073741824, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellVisualID_1': 11711, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


lichborne_49039 = spell(
    id=49039,
    name='Lichborne',
    school=School.SHADOW,
    attributes=262144,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=5),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=10),
    ],
    spell_icon_id=61,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 163872, 'AttributesEx5': 393224, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Immune to Charm, Fear and Sleep.\r\nUndead.', 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Draw upon unholy energy to become undead for $d.  While undead, you are immune to Charm, Fear and Sleep effects.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 601, 'SpellClassMask_2': 16, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellVisualID_1': 11706},
)


hungering_cold_49203 = spell(
    id=49203,
    name='Hungering Cold',
    school=School.FROST,
    dispel=DispelType.MAGIC,
    attributes=1310720,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    power_type=PowerType.RUNIC_POWER,
    mana_cost=400,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=1, implicit_target_b=18, radius_yards=0.0),
    ],
    spell_icon_id=2797,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 262280, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Frozen.', 'BaseLevel': 55, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Purges the earth around the Death Knight of all heat.  Enemies within $51209a1 yards are trapped in ice, preventing them from performing any action for $51209d and infecting them with Frost Fever.  Enemies are considered Frozen, but any damage other than diseases will break the ice.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectRadiusIndex_1': 36, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 36864, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellVisualID_1': 11156, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


summon_gargoyle_49206 = spell(
    id=49206,
    name='Summon Gargoyle',
    school=School.SHADOW,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    power_type=PowerType.RUNIC_POWER,
    mana_cost=600,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=40000,
    effects=[
        Effect(type=EffectType.SUMMON, implicit_target_a=44, misc_value=27829, radius_yards=3.0),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=6, apply_aura=226, amplitude=1000),
        Effect(type=EffectType.TRIGGER_SPELL, base_points=2, implicit_target_a=1, trigger_spell=61777),
    ],
    spell_icon_id=1577,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx5': 1024, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Under attack from a Gargoyle.', 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "A Gargoyle flies into the area and bombards the target with Nature damage modified by the Death Knight's attack power.  Persists for $61777d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 209, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RuneCostID': 652, 'SpellClassMask_2': 128, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellVisualID_1': 11833, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


bone_shield_49222 = spell(
    id=49222,
    name='Bone Shield',
    school=School.NATURE,
    attributes=262144,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=79, misc_value=127),
    ],
    spell_icon_id=2739,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx4': 524352, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage reduced by $s1%.', 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The Death Knight is surrounded by $n whirling bones.  While at least 1 bone remains, $Ghe:she; takes $s1% less damage from all sources and deals $s2% more damage with all attacks, spells and abilities.  Each damaging attack that lands consumes 1 bone.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 3, 'ProcTypeMask': 172712, 'RangeIndex': 1, 'RuneCostID': 654, 'SpellClassMask_2': 64, 'SpellClassSet': 15, 'SpellVisualID_1': 11539, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


deathchill_49796 = spell(
    id=49796,
    name='Deathchill',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=2028,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx5': 32, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next Icy Touch, Howling Blast, Frost Strike or Obliterate has a 100% chance to critically hit.', 'BaseLevel': 55, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When activated, makes your next Icy Touch, Howling Blast, Frost Strike or Obliterate a critical hit if used within $d.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 2, 'EffectSpellClassMaskA_2': 131078, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 349456, 'RangeIndex': 1, 'RuneCostID': 743, 'SpellClassMask_2': 1, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellVisualID_1': 11515},
)


anti_magic_zone_51052 = spell(
    id=51052,
    name='Anti-Magic Zone',
    school=School.SHADOW,
    attributes=262144,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=45000,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=9999, mechanic=26, implicit_target_a=18, misc_value=28306),
    ],
    spell_icon_id=3144,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Places a large, stationary Anti-Magic Zone that reduces spell damage done to party or raid members inside it by $50461s1%.  The Anti-Magic Zone lasts for $51052d or until it absorbs ${$51052m1+2*$AP} spell damage.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectMiscValueB_1': 121, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 854, 'SpellClassMask_2': 524288, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellVisualID_1': 8116},
)


unbreakable_armor_51271 = spell(
    id=51271,
    name='Unbreakable Armor',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=101, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=137),
    ],
    spell_icon_id=2703,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Armor increased by $s1%.\r\nStrength increased by $s2%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reinforces your armor with a thick coat of ice, increasing your armor by $s1% and increasing your Strength by $s2% for $d.', 'EffectBasePoints_3': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 1202, 'SpellClassMask_1': 2097152, 'SpellClassSet': 15, 'SpellVisualID_1': 44},
)


vampiric_blood_55233 = spell(
    id=55233,
    name='Vampiric Blood',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=34, implicit_target_a=1, apply_aura=AuraType.MOD_HEALING_PCT, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=34),
    ],
    spell_icon_id=153,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Healing improved by $s1%\r\nMaximum health increased by $s2%', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Temporarily grants the Death Knight $s2% of maximum health and increases the amount of health generated through spells and effects by $s1% for $d.  After the effect expires, the health is lost.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 1203, 'SpellClassMask_2': 8, 'SpellClassSet': 15, 'SpellVisualID_1': 11149},
)


ghoul_frenzy_63560 = spell(
    id=63560,
    name='Ghoul Frenzy',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=10000,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=9,
    range_yards=45.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=5, apply_aura=20, amplitude=3000),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=5, apply_aura=138),
    ],
    spell_icon_id=108,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx4': 64, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Decreases the time between attacks by $s2% and heals $s1% every $t1 sec.', 'BaseLevel': 26, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Grants your pet $s2% haste for $d and  heals it for ${$m1*10}% of its health over the duration.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RuneCostID': 1764, 'SpellClassMask_3': 32, 'SpellClassSet': 15, 'SpellLevel': 26, 'SpellPriority': 50, 'SpellVisualID_1': 13440, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetCreatureType': 32},
)
