"""
Deathknight - player-castable spells (real cast_time_ms/cooldown_ms, not marked passive).

Split from a single source/classes/deathknight.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .deathknight_...` below) resolve.
"""

from lib.dsl import AuraType, DispelType, Effect, EffectType, Mechanic, PowerType, School
from lib.dsl.registry import const, pot_text, procs_on, scripted_by, spell, unbind_script

from . import _masks as m
from .deathknight_blood import sanguine_ground_tooltip_1252
from .deathknight_shared import anti_magic_zone_50461


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
    tooltip_vars=sanguine_ground_tooltip_1252,  # S1a U24: tooltip only (Sanguine Ground +10/20/30%); the row stays stock
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 60); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 4 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 136, 'AttributesEx5': 512, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s1 Shadow damage inflicted every sec.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Corrupts the ground targeted by the Death Knight, causing ${$m1*$<sang>} Shadow damage every sec that targets remain in the area for $d.  This ability produces a high amount of threat.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RuneCostID': 101, 'SpellClassMask_1': 32, 'SpellClassSet': 15, 'SpellLevel': 30, 'SpellVisualID_1': 9735, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Targets': 64},
)
scripted_by(43265, 'spell_dk_death_and_decay_blood')
scripted_by(52212, 'spell_dk_death_and_decay_tick_blood')


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
    raw_overrides={'AttributesEx': 132096, 'AttributesEx2': 1, 'AttributesEx3': 262144, 'AttributesEx5': 2097152, 'AttributesEx6': 32, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'A Risen Ghoul is in your service.', 'BaseLevel': 12, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Raises a Ghoul to fight by your side.  You can have a maximum of one Ghoul at a time.  Lasts $46585d.', 'EffectBasePoints_1': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_1': 1, 'EquippedItemClass': -1, 'ImplicitTargetA_1': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RuneCostID': 341, 'SpellClassMask_1': 4096, 'SpellClassSet': 15, 'SpellLevel': 12, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
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
    cooldown_ms=180000,
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
    raw_overrides={'AttributesEx': 1024, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 54, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Empower your rune weapon, immediately activating all your runes and generating 25 Runic Power.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 1144, 'Speed': 1.0, 'SpellClassMask_1': m.ERW, 'SpellClassSet': 15, 'SpellLevel': 54, 'SpellVisualID_1': 10590},
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
        Effect(type=EffectType.APPLY_AURA, sp_potency=7.1, potency_kind='absorb', mechanic=26, implicit_target_a=1, apply_aura=69, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=267, misc_value=126),
    ],
    spell_icon_id=99,
    notes=(
        'pulled from existing data; potency-system (PLAN P7 Death Knight pass, 2026-10-01): '
        'converted eff1 (SCHOOL_ABSORB) to sp_potency=7.1 (deathknight-potency-report.md\'s '
        'base-damage-implied default; old EffectBonusMultiplier was 0, no mismatch).'
    ),
    raw_overrides={'AttributesEx4': 64, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Spell damage reduced by $s1%.\r\nImmune to magic debuffs.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Surrounds the Death Knight in an Anti-Magic Shell, absorbing $48707s1% of the damage dealt by harmful spells (up to a maximum of $s2% of the Death Knight's health) and preventing application of harmful magical effects.  Damage absorbed by Anti-Magic Shell energizes the Death Knight with additional runic power.  Lasts $48707d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 522, 'SpellClassMask_1': 131072, 'SpellClassSet': 15, 'SpellLevel': 46, 'SpellVisualID_1': 11869},
)
scripted_by(anti_magic_shell_48707, 'spell_dk_ams_damage_record')


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
        Effect(type=EffectType.HEAL, sp_potency=3.8, potency_kind='heal', implicit_target_a=1),
    ],
    spell_icon_id=169,
    notes=(
        'pulled from existing data; potency-system (PLAN P7 Death Knight pass, 2026-10-01): '
        'converted eff3 (HEAL) to sp_potency=3.8 (deathknight-potency-report.md\'s '
        'base-damage-implied default; old EffectBonusMultiplier was 0, no mismatch).'
    ),
    raw_overrides={'AttributesEx': 656384, 'AttributesEx2': 536870916, 'AttributesEx3': 1048576, 'AttributesEx4': 16, 'AttributesEx5': 2097152, 'AuraDescription_Lang_Mask': 16712172, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Sacrifices an undead minion, healing the Death Knight for $s3% of $Ghis:her; maximum health.  This heal cannot be a critical.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 541, 'SpellClassMask_1': 524288, 'SpellClassSet': 15, 'SpellLevel': 38, 'SpellVisualID_1': 11150, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
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
        Effect(type=31, weapon_potency=149, implicit_target_a=6),
    ],
    spell_icon_id=3007,
    notes=(
        'pulled from existing data; potency-system (PLAN P7 Death Knight pass, PLAN F11 '
        'hard-coded-AP audit, 2026-10-01): eff2 (WEAPON_PERCENT_DAMAGE) converted to '
        'weapon_potency=149 (same pre-existing off-by-one fix as Mangle/Swipe/Shred - '
        'base_points=149 with the default die_sides=1 was actually dealing 150% live; '
        'weapon_potency\'s own -1/+1 convention lands on the intended 149%). '
        'SpellEffects.cpp\'s hard-coded Rune Strike bonus (spell_bonus += 0.15*AP, in '
        'Spell::EffectWeaponDmg\'s SPELLFAMILY_DEATHKNIGHT case) is now gated behind '
        'SpellPotency::HasRow() and DROPPED once converted, not replaced - '
        'docs/potency-system.md\'s "Weapon attacks": explicit attack-power bonuses on '
        'weapon strikes are removed, not folded into weapon_potency ("a designer who wants '
        'more scaling raises the weapon percent instead"), same treatment as Ferocious '
        'Bite/Eviscerate\'s own dropped AP terms in P6. The hidden tier-2 EffectBasePoints_3=9 '
        'constant (used only by the now-dropped tooltip approximation $m2*$AP*$m3/10000, which '
        'never matched the real 0.15*AP hard-code even before this change) is removed as dead.'
    ),
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AttributesEx4': 512, 'AuraDescription_Lang_Mask': 16712188, 'CasterAuraSpell': 56817, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Strike the target for $s2% weapon damage.  Only usable after the Death Knight dodges or parries.  Can't be dodged, blocked, or parried.  This attack causes a high amount of threat.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'RangeIndex': 2, 'SpellClassMask_2': 536870912, 'SpellClassSet': 15, 'SpellLevel': 14, 'SpellVisualID_1': 39},
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
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=60, implicit_target_a=6),
        Effect(type=EffectType.NORMALIZED_WEAPON_DMG, sp_potency=5, potency_kind='direct', time_basis_ms=1500,
               implicit_target_a=6),
    ],
    spell_icon_id=2740,
    notes=(
        'pulled from existing data; dk-rework DK0a (shared doc "Frost Strike", U8/U9): baseline at level 10, '
        '60% weapon damage plus 5 potency Frost damage. Percent effect FIRST, flat NORMALIZED_WEAPON_DMG effect '
        'second (SpellEffects.cpp EffectWeaponDmg multiplies a flat effect that sits before the percent effect '
        'by the percent, so the flat lands whole here). The old single-rank bootstrap values (86 + 6.52/level '
        'flat, 54% weapon) are gone; the stale EffectSpellClassMaskC_2 twin (no aura on effect 2) is dropped. '
        'EFFECT_3 stays empty. 40 RP cost (PowerType 6 / ManaCost 400), RuneCostID 621 (0,0,0,0) kept.'
    ),
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly strike the enemy, dealing $s1% weapon damage plus {pot2.avg} as Frost damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'RuneCostID': 621, 'SpellClassMask_2': m.FROST_STRIKE, 'SpellClassSet': 15, 'SpellLevel': 10, 'SpellVisualID_1': 11612, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)

scripted_by(frost_strike_49143, 'spell_dk_frost_strike_rework')  # S2a: Frost multiplier, school/Razorice terms, off-hand copy


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
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=62, potency_kind='direct', implicit_target_a=53, implicit_target_b=16, radius_yards=10.0),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=53, implicit_target_b=16, radius_yards=10.0,
               trigger_spell=55095),
    ],
    spell_icon_id=2131,
    notes=(
        'pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept '
        'from rank 1 (learn level 55); RealPointsPerLevel from rank1->covers-60-overridden '
        '(undershoot-vs-top-rank) (anchor rank 4 @ level 80); coefficient/cast_time_ms/'
        'mana_cost_pct from max rank. potency-system (PLAN P7 Death Knight pass, 2026-10-01): '
        'eff2 (SCHOOL_DAMAGE) converted to ap_potency=100.9 (deathknight-potency-report.md / '
        'deathknight-potency-proposals.txt - mismatch row, old AP-coefficient-implied potency '
        'was 46.7, the base-damage-implied 100.9 wins per the user-reviewed proposal). DieSides '
        '17 replaced by the system-standard +-5% roll. dk-rework S2a (U8): 62 AP potency (S2 TUNE 2026-10-25, U33; '
        'was 90) at SpellLevel 20, 10 yd radius, '
        '20 yd range, RuneCostID 647 (1 Unholy + 1 Frost, +15 RP, stock), 8 s cooldown / category 1248; eff2 = '
        'TRIGGER_SPELL 55095 on the same area targets (fires per target at launch, before the damage, so Glacier Rot '
        'always counts); the stale EffectBasePoints_3 / EffectSpellClassMaskC_1 twins are dropped. Rime keeps its '
        'EFFECT_1 trigger of Freezing Fog 59052 (a SPELLMOD_COST on this spell).'
    ),
    raw_overrides={'AttributesEx': 134217864, 'AttributesEx6': 1024, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Blast the target with a frigid wind, dealing {pot2} Frost damage to all enemies within 10 yards and infecting them with Frost Fever.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 14684919, 'EffectSpellClassMaskB_1': 12589815, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RuneCostID': 647, 'SpellClassMask_2': 2, 'SpellClassSet': 15, 'SpellLevel': 20, 'SpellPriority': 50, 'SpellVisualID_1': 11617, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)

scripted_by(howling_blast_49184, 'spell_dk_howling_blast_rework')  # S2a (U8): Rime / Deathchill notes, Frost multiplier, Avalanche, RotFC, Hungering Cold storm


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
        Effect(type=EffectType.ENERGIZE, base_points=499, implicit_target_a=1, misc_value=6),
    ],
    spell_icon_id=2726,
    notes=(
        'pulled from existing data; dk-rework DK0a (shared doc "Rune Tap"): baseline at level 18. Effect index 0 '
        'HEAL_PCT -> ENERGIZE Runic Power (misc 6), stored 499 = 500 = 50 RP (RP x10); heals nothing. Effect index '
        '0 on purpose: Final Roar (S2) targets it with SPELLMOD_EFFECT1. 1 Blood Rune (RuneCostID 581), 60 s, off '
        'GCD kept. The stock spell_dk_rune_tap_party binding on 59754 is unbound below.'
    ),
    raw_overrides={'AttributesEx2': 570425344, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 18, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Converts 1 Blood Rune into ${$s1/10} Runic Power.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 581, 'SpellClassMask_1': m.RUNE_TAP, 'SpellClassSet': 15, 'SpellLevel': 18, 'SpellVisualID_1': 11512},
)
unbind_script(59754, 'spell_dk_rune_tap_party')


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
    notes='pulled from existing data; dk-rework S1a (Blood doc "Mark of Blood"): ProcCharges 20 -> 10 raw (lasts up to 10 hits, '
          'was 20); tooltip "Lasts 20 sec or up to 10 hits."; icon 2285, d0 b28 unchanged',
    raw_overrides={'AttributesEx': 134218752, 'AttributesEx3': 67305473, 'AttributesEx4': 1572864, 'AttributesEx5': 32, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Hits by this target restore $s2% health.', 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Place a Mark of Blood on an enemy.  Whenever the marked enemy deals damage to a target, that target is healed for $49005s2% of its maximum health.  Lasts 20 sec or up to 10 hits.', 'EffectBasePoints_2': 3, 'EffectBasePoints_3': 299, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcCharges': 10, 'ProcTypeMask': 332116, 'RuneCostID': 583, 'SpellClassMask_1': 268435456, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50, 'SpellVisualID_1': 11513, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
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
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.SUMMON, implicit_target_a=64, misc_value=27893, radius_yards=2.0),
        Effect(type=EffectType.APPLY_AURA, base_points=50706, implicit_target_a=1, apply_aura=AuraType.DUMMY, trigger_spell=1206),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=6, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2657,
    notes='pulled from existing data; dk-rework S1a (Blood doc "Dancing Rune Weapon"): no Runic Power cost (was 60, mana_cost 600 -> 0), '
          '90 s cooldown, 12 s duration (both already stock); tooltip adds the +20% parry (buff 203156, linked by blood_b.py). '
          'Script rebound below to spell_dk_dancing_rune_weapon_rework.',
    raw_overrides={'AttributesEx3': 67109890, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'You have recently summoned a rune weapon.', 'BaseLevel': 55, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a second rune weapon that fights on its own for $d, mirroring your attacks for $51906s3% reduced damage. While active, your parry chance is increased by $203156s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 208, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 86288, 'SpellClassMask_1': 1073741824, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellVisualID_1': 11711, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
unbind_script(49028, 'spell_dk_dancing_rune_weapon')
scripted_by(49028, 'spell_dk_dancing_rune_weapon_rework')


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
    raw_overrides={'AttributesEx': 163872, 'AttributesEx5': 393224, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Immune to Charm, Fear and Sleep. Undead.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Draw upon unholy energy to become undead for $d. While undead, you are immune to Charm, Fear and Sleep effects.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 601, 'SpellClassMask_2': m.LICHBORNE, 'SpellClassSet': 15, 'SpellLevel': 20, 'SpellVisualID_1': 11706},
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


BONE_SHIELD_MAX_CHARGES = const(
    'BONE_SHIELD_MAX_CHARGES', 6,
    'Most charges Bone Shield can hold (Marrowrend adds up to this; the spell itself starts at ProcCharges 3) [tune].',
    cpp_type='uint32',
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
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.MOD_RESISTANCE_PCT, misc_value=1),
    ],
    spell_icon_id=2739,
    notes=(
        'pulled from existing data; dk-rework DK0a (shared doc "Bone Shield", U11): the shared Death Knight tank '
        'aura, no cast of its own (the Unholy talent is retired; S1 Marrowrend applies it). Effect index 0 is '
        'MOD_RESISTANCE_PCT misc 1 (armor) +30% (stored 29); the stock -20% damage taken and +2% damage done '
        'effects are gone. 30 s (was 300 s). ProcCharges 3, S1 raises it up to BONE_SHIELD_MAX_CHARGES. '
        'spell_proc: taken melee/ranged auto + melee/ranged class spells only (0x2A8, no magic), type DAMAGE, '
        '2 s cooldown, no phase mask (LoadSpellProcs ignores it for taken-hit flags), HitMask 0x403 (NORMAL | CRITICAL | ABSORB: NOT the default; '
        'an absorbed melee swing still consumes a charge). '
        'Charges show as the stack count natively.'
    ),
    raw_overrides={'AttributesEx': 1024, 'AttributesEx4': 524352, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Armor increased. Each damaging melee or ranged attack that hits you consumes a charge.', 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Surrounds you with a barrier of whirling bones, increasing your armor by $s1%. Each damaging melee or ranged attack that hits you consumes a charge, no more than once every 2 sec. Lasts $d or until all charges are consumed.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 3, 'ProcTypeMask': 680, 'RangeIndex': 1, 'RuneCostID': 654, 'SpellClassMask_2': m.BONE_SHIELD, 'SpellClassSet': 15, 'SpellVisualID_1': 11539, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
procs_on(
    bone_shield_49222, proc_flags=0x2A8, spell_type_mask=1, hit_mask=0x403, cooldown_ms=2000,
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
    notes=(
        'pulled from existing data; dk-rework DK0a (shared doc "Anti-Magic Zone"): baseline at level 52, 1 Unholy Rune '
        '(RuneCostID 854), 0 Runic Power (stock), 2 min, on the GCD (133 / 1500, shared doc). This is the summoner only; the area aura 50461 (deathknight_shared.py) '
        'owns the 75% reduction and the 500 attack-power-potency absorb pool. Stale EffectBasePoints_2 / EffectDieSides_2 '
        'twins removed (Effect 2 is empty). EffectMiscValueB_1 121 (SummonProperties) and the summon\'s 9999 are kept.'
    ),
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 52, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Places a large, stationary Anti-Magic Zone that reduces spell damage taken by party or raid members inside it by 75%. The zone lasts $51052d or until it absorbs ' + pot_text(anti_magic_zone_50461) + ' spell damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 121, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 854, 'SpellClassMask_2': m.AMZ, 'SpellClassSet': 15, 'SpellLevel': 52, 'SpellVisualID_1': 8116, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
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
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Maximum health and healing received increased.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Temporarily grants you $s2% of your maximum health and increases the healing you receive from spells and effects by $s1% for $d.  When the effect ends, the health is lost.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 1203, 'SpellClassMask_2': 8, 'SpellClassSet': 15, 'SpellVisualID_1': 11149},
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
