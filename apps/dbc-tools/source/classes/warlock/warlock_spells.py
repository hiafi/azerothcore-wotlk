"""
Warlock - player-castable spells (real cast_time_ms/cooldown_ms, not marked passive).

Split from a single source/classes/warlock.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .warlock_...` below) resolve.
"""

from lib.dsl import AuraType, DispelType, Effect, EffectType, Mechanic, PowerType, School
from lib.dsl.registry import spell
from .warlock_trigger_spells import hellfire_effect_5857, rain_of_fire_42223


eye_of_kilrogg_126 = spell(
    id=126,
    name='Eye of Kilrogg',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=5000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=4,
    range_yards=50000.0,
    duration_ms=45000,
    effects=[
        Effect(type=EffectType.SUMMON, implicit_target_a=32, misc_value=4277, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=135,
    notes='pulled from existing data',
    raw_overrides={'ActiveIconID': 135, 'AttributesEx': 139268, 'AttributesEx2': 4, 'AttributesEx4': 65536, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Controlling Eye of Kilrogg.', 'BaseLevel': 22, 'CastingTimeIndex': 6, 'ChannelInterruptFlags': 15420, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons an Eye of Kilrogg and binds your vision to it.  The eye moves quickly but is very fragile.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 65, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Summon', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_3': 64, 'SpellClassSet': 5, 'SpellLevel': 22, 'SpellPriority': 50, 'SpellVisualID_1': 350, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


detect_invisibility_132 = spell(
    id=132,
    name='Detect Invisibility',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=2,
    range_yards=30.0,
    duration_ms=600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=999, implicit_target_a=21, apply_aura=19),
    ],
    spell_icon_id=209,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Detect lesser invisibility.', 'BaseLevel': 26, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Allows the friendly target to detect lesser invisibility for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_3': 64, 'SpellClassSet': 5, 'SpellLevel': 26, 'SpellPriority': 50, 'SpellVisualID_1': 140, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


corruption_172 = spell(
    id=172,
    name='Corruption',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=14,
    range_yards=30.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, points_per_level=2.267857142857143, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
        Effect(type=EffectType.DUMMY, die_sides=0),
    ],
    spell_icon_id=313,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 4); RealPointsPerLevel from rank1->covers-60 (anchor rank 7 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s1 Shadow damage every $t1 seconds.', 'BaseLevel': 4, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Corrupts the target, causing $o1 Shadow damage over $d.', 'EffectBonusMultiplier_1': 0.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 2, 'SpellClassSet': 5, 'SpellLevel': 4, 'SpellPriority': 50, 'SpellVisualID_1': 8629, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


immolate_348 = spell(
    id=348,
    name='Immolate',
    school=School.FIRE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=2000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=17,
    range_yards=30.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, points_per_level=1.9367088607594938, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=7, points_per_level=5.7215189873417724, implicit_target_a=6),
        Effect(type=77, die_sides=0, implicit_target_a=6),
    ],
    spell_icon_id=31,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 11 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx4': 1048576, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s1 Fire damage every $t1 seconds.', 'BaseLevel': 1, 'CastingTimeIndex': 5, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Burns the enemy for $s2 Fire damage and then an additional $o1 Fire damage over $d.', 'EffectBonusMultiplier_2': 0.20000000298023224, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 4, 'SpellClassSet': 5, 'SpellLevel': 1, 'SpellVisualID_1': 46, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


curse_of_doom_603 = spell(
    id=603,
    name='Curse of Doom',
    school=School.SHADOW,
    dispel=DispelType.CURSE,
    attributes=65536,
    category=1179,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=60000,
    mana_cost=0,
    mana_cost_pct=15,
    range_yards=30.0,
    duration_ms=60000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3199, points_per_level=205.0, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=60000),
    ],
    spell_icon_id=91,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 60); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 3 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Causes $s1 Shadow damage after $d.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Curses the target with impending doom, causing $s1 Shadow damage after $d.  If the target yields experience or honor when it dies from this damage, a Doomguard will be summoned.  Cannot be cast on players.', 'EffectBonusMultiplier_1': 2.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 2, 'SpellClassSet': 5, 'SpellLevel': 60, 'SpellVisualID_1': 5019, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


shadow_bolt_686 = spell(
    id=686,
    name='Shadow Bolt',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=17,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=11, points_per_level=7.966101694915254, die_sides=5, implicit_target_a=6),
    ],
    spell_icon_id=213,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60 (anchor rank 10 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 90, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Sends a shadowy bolt at the enemy, causing $s1 Shadow damage.', 'EffectBonusMultiplier_1': 0.8569999933242798, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 20.0, 'SpellClassMask_1': 1, 'SpellClassSet': 5, 'SpellLevel': 1, 'SpellVisualID_1': 64, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


demon_skin_687 = spell(
    id=687,
    name='Demon Skin',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=31,
    range_yards=0.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=89, points_per_level=2.9661016949152543, implicit_target_a=1, apply_aura=22, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.MOD_HEALING_PCT, misc_value=127),
    ],
    spell_icon_id=89,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases armor by $s1, and amount of health generated through spells and effects by $s2%', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Protects the caster, increasing armor by $s1, and increasing the amount of health generated through spells and effects by $s2%. Only one type of Armor spell can be active on the Warlock at any time.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_3': 16, 'SpellClassSet': 5, 'SpellLevel': 1, 'SpellVisualID_1': 130, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


summon_imp_688 = spell(
    id=688,
    name='Summon Imp',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=10000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=64,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=56, base_points=-1, implicit_target_a=32, misc_value=416),
    ],
    spell_icon_id=215,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131073, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons an Imp under the command of the Warlock.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Summon', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 536870912, 'SpellClassSet': 5, 'SpellLevel': 1, 'SpellVisualID_1': 4043, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


drain_life_689 = spell(
    id=689,
    name='Drain Life',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=17,
    range_yards=30.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, points_per_level=1.8636363636363635, implicit_target_a=6, apply_aura=AuraType.PERIODIC_LEECH, amplitude=1000),
    ],
    spell_icon_id=546,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 14); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 16388, 'AttributesEx5': 8192, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Drains $s1 health every $t1 sec to the caster.', 'BaseLevel': 14, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31756, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Transfers $s1 health every $t1 sec from the target to the caster.  Lasts $d.', 'EffectBonusMultiplier_1': 0.14300000667572021, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 8, 'SpellClassSet': 5, 'SpellLevel': 14, 'SpellVisualID_1': 12655, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


create_soulstone_693 = spell(
    id=693,
    name='Create Soulstone',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=68,
    range_yards=0.0,
    effects=[
        Effect(type=24, implicit_target_a=1),
    ],
    spell_icon_id=92,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 18); RealPointsPerLevel from rank1->covers-60 (anchor rank 5 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx4': 65536, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 18, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Creates a Minor Soulstone.  The Soulstone can be used to store one target's soul.  If the target dies while his soul is stored, he will be able to resurrect with $3026s1 health and $3026q1 mana.\r\n\r\nConjured items disappear if logged out for more than 15 minutes.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 5232, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ReagentCount_1': 1, 'Reagent_1': 6265, 'SpellClassMask_1': 1048576, 'SpellClassSet': 5, 'SpellLevel': 18, 'SpellVisualID_1': 138, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


ritual_of_summoning_698 = spell(
    id=698,
    name='Ritual of Summoning',
    school=School.SHADOW,
    attributes=268500992,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=12,
    range_yards=30.0,
    duration_ms=120000,
    effects=[
        Effect(type=50, die_sides=0, implicit_target_a=47, misc_value=194108, radius_yards=0.0),
    ],
    spell_icon_id=164,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131076, 'AttributesEx3': 1073741824, 'AttributesEx4': 65536, 'AttributesEx5': 8192, 'AttributesEx6': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 15374, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Begins a ritual that creates a summoning portal.  The summoning portal can be used by 2 party or raid members to summon a targeted party or raid member.  The ritual portal requires the caster and 2 additional party or raid members to complete.  In order to participate, all players must be out of combat and right-click the portal and not move until the ritual is complete.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectRadiusIndex_1': 36, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 6265, 'SpellClassMask_3': 64, 'SpellClassSet': 5, 'SpellLevel': 20, 'SpellVisualID_1': 1523, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


curse_of_weakness_702 = spell(
    id=702,
    name='Curse of Weakness',
    school=School.SHADOW,
    dispel=DispelType.CURSE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=30.0,
    duration_ms=120000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-22, points_per_level=-6.0131578947368425, implicit_target_a=6, apply_aura=AuraType.MOD_ATTACK_POWER),
        Effect(type=EffectType.APPLY_AURA, base_points=-6, implicit_target_a=6, apply_aura=101, misc_value=1),
    ],
    spell_icon_id=543,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 4); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Melee attack power reduced by $s1, and armor is reduced by $s2%.', 'BaseLevel': 4, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Target's melee attack power is reduced by $s1 and armor is reduced by $s2% for $d.  Only one Curse per Warlock can be active on any one target.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 32768, 'SpellClassSet': 5, 'SpellLevel': 4, 'SpellVisualID_1': 346, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


demon_armor_706 = spell(
    id=706,
    name='Demon Armor',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=31,
    range_yards=0.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=464, points_per_level=27.25, implicit_target_a=1, apply_aura=22, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.MOD_HEALING_PCT, misc_value=127),
    ],
    spell_icon_id=89,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 8 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases armor by $s1, and amount of health generated through spells and effects by $s2%', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Protects the caster, increasing armor by $s1, and increasing the amount of health generated through spells and effects by $s2%. Only one type of Armor spell can be active on the Warlock at any time.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 32, 'SpellClassSet': 5, 'SpellLevel': 20, 'SpellVisualID_1': 130, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


banish_710 = spell(
    id=710,
    name='Banish',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    mechanic=Mechanic.BANISH,
    attributes=1073807360,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=30.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=39, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=6, apply_aura=AuraType.MOD_HEALING_PCT, misc_value=127),
    ],
    spell_icon_id=96,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 28); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 65536, 'AttributesEx2': 64, 'AttributesEx5': 32, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Invulnerable, but unable to act.', 'BaseLevel': 28, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Banishes the enemy target, preventing all action but making it invulnerable for up to $d.  Only one target can be banished at a time.  Casting Banish on a banished target will cancel the spell.  Only works on Demons and Elementals.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 134217728, 'SpellClassSet': 5, 'SpellLevel': 28, 'SpellVisualID_1': 1305, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetCreatureType': 12},
)


health_funnel_755 = spell(
    id=755,
    name='Health Funnel',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.HEALTH,
    mana_cost=11,
    mana_cost_pct=0,
    range_yards=45.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, points_per_level=7.470588235294118, implicit_target_a=5, apply_aura=AuraType.PERIODIC_HEAL, amplitude=1000),
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=88),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=5, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
    ],
    spell_icon_id=153,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 12); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 16388, 'AttributesEx2': 2056, 'AttributesEx5': 8192, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Transferring Life.', 'BaseLevel': 12, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31756, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Gives $s1 health to the caster's pet every second for $d as long as the caster channels.", 'EffectBonusMultiplier_1': 0.5379999876022339, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 2.200000047683716, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'ManaPerSecond': 5, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 16777216, 'SpellClassSet': 5, 'SpellLevel': 12, 'SpellVisualID_1': 163, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


curse_of_agony_980 = spell(
    id=980,
    name='Curse of Agony',
    school=School.SHADOW,
    dispel=DispelType.CURSE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=30.0,
    duration_ms=24000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=6, points_per_level=1.9166666666666667, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=2000),
    ],
    spell_icon_id=544,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 8); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx3': 128, 'AttributesEx4': 1048576, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$o1 Shadow damage over $d.', 'BaseLevel': 8, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Curses the target with agony, causing $o1 Shadow damage over $d.  This damage is dealt slowly at first, and builds up as the Curse reaches its full duration.  Only one Curse per Warlock can be active on any one target.', 'EffectBonusMultiplier_1': 0.10000000149011612, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 1024, 'SpellClassSet': 5, 'SpellLevel': 8, 'SpellVisualID_1': 824, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


immolate_1094 = spell(
    id=1094,
    name='Immolate',
    school=School.FIRE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=2000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=17,
    range_yards=30.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=17, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=44, points_per_level=1.5, implicit_target_a=6),
        Effect(type=77, die_sides=0, implicit_target_a=6),
    ],
    spell_icon_id=31,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid)',
    raw_overrides={'AttributesEx4': 1048576, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s1 Fire damage every $t1 seconds.', 'BaseLevel': 20, 'CastingTimeIndex': 5, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Burns the enemy for $s2 Fire damage and then an additional $o1 Fire damage over $d.', 'EffectBonusMultiplier_2': 0.20000000298023224, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 25, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 4, 'SpellClassSet': 5, 'SpellLevel': 20, 'SpellVisualID_1': 46, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


enslave_demon_1098 = spell(
    id=1098,
    name='Enslave Demon',
    school=School.SHADOW,
    mechanic=Mechanic.CHARM,
    attributes=1073807360,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=27,
    range_yards=30.0,
    duration_ms=300000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=31, points_per_level=1.0666666666666667, implicit_target_a=6, apply_aura=6),
        Effect(type=EffectType.APPLY_AURA, base_points=-31, mechanic=8, implicit_target_a=6, apply_aura=138),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=6, apply_aura=65),
    ],
    spell_icon_id=1500,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 30); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131073, 'AttributesEx2': 64, 'AttributesEx4': 536872960, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Enslaved.', 'BaseLevel': 30, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Enslaves the target demon, up to level $m1, forcing it to do your bidding.  While enslaved, the time between the demon's attacks is increased by $s2% and its casting speed is slowed by $s3%.  Lasts up to $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 6265, 'SpellClassMask_1': 2048, 'SpellClassSet': 5, 'SpellLevel': 30, 'SpellVisualID_1': 1266, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetCreatureType': 4},
)


drain_soul_1120 = spell(
    id=1120,
    name='Drain Soul',
    school=School.SHADOW,
    attributes=65537,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=14,
    range_yards=30.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=6, apply_aura=86),
        Effect(type=EffectType.APPLY_AURA, base_points=10, points_per_level=1.8714285714285714, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL),
    ],
    spell_icon_id=113,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 67256324, 'AttributesEx3': 134217728, 'AttributesEx5': 8192, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s2 Shadow damage every $t2 seconds.', 'BaseLevel': 10, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31756, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Drains the soul of the target, causing $o2 Shadow damage over $d.  If the target is at or below 25% health, Drain Soul causes four times the normal damage. If the target dies while being drained, and yields experience or honor, the caster gains a Soul Shard.  Each time the Drain Soul damages the target, it also has a chance to generate a Soul Shard.  Soul Shards are required for other spells.', 'EffectBonusMultiplier_2': 0.42899999022483826, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 6265, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 2, 'SpellClassMask_1': 16384, 'SpellClassSet': 5, 'SpellLevel': 10, 'SpellVisualID_1': 12656, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


curse_of_the_elements_1490 = spell(
    id=1490,
    name='Curse of the Elements',
    school=School.SHADOW,
    dispel=DispelType.CURSE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=30.0,
    duration_ms=300000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-46, points_per_level=-2.5, implicit_target_a=6, apply_aura=22, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=5, points_per_level=0.14583333333333334, implicit_target_a=6, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
    ],
    spell_icon_id=55,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 32); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx5': 4, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Reduces Arcane, Fire, Frost, Nature and Shadow resistances by $s1.  Increases magic damage taken by $s2%.', 'BaseLevel': 32, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Curses the target for $d, reducing Arcane, Fire, Frost, Nature, and Shadow resistances by $s1 and increasing magic damage taken by $s2%.  Only one Curse per Warlock can be active on any one target.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 512, 'SpellClassSet': 5, 'SpellLevel': 32, 'SpellVisualID_1': 785, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


curse_of_tongues_1714 = spell(
    id=1714,
    name='Curse of Tongues',
    school=School.SHADOW,
    dispel=DispelType.CURSE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=4,
    range_yards=30.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-26, points_per_level=-0.14705882352941177, implicit_target_a=6, apply_aura=216),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=75, misc_value=8),
    ],
    spell_icon_id=692,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 26); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx4': 536872960, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Speaking Demonic increasing casting time by $s1%.', 'BaseLevel': 26, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Forces the target to speak in Demonic, increasing the casting time of all spells by $s1%.  Only one Curse per Warlock can be active on any one target.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 2147483648, 'SpellClassMask_3': 2048, 'SpellClassSet': 5, 'SpellLevel': 26, 'SpellPriority': 50, 'SpellVisualID_1': 339, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


hellfire_1949 = spell(
    id=1949,
    name='Hellfire',
    school=School.FIRE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=64,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=1000, trigger_spell=hellfire_effect_5857.id),
        Effect(type=EffectType.APPLY_AURA, base_points=82, points_per_level=7.4, implicit_target_a=1, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=1000),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=16),
    ],
    spell_icon_id=937,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 30); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 98368, 'AttributesEx5': 8192, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damages self and all nearby enemies.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31756, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Ignites the area surrounding the caster, causing $1949s2 Fire damage to $ghimself:herself; and $5857s1 Fire damage to all nearby enemies every $1949t2 sec.  Lasts $1949d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 0.0949999988079071, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 64, 'SpellClassSet': 5, 'SpellLevel': 30, 'SpellVisualID_1': 5423, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


create_spellstone_2362 = spell(
    id=2362,
    name='Create Spellstone',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=5000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=45,
    range_yards=0.0,
    effects=[
        Effect(type=24, implicit_target_a=1),
    ],
    spell_icon_id=344,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 36); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx5': 2, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 36, 'CastingTimeIndex': 6, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While applied to target weapon it increases damage dealt by periodic spells by $55172s1% and spell haste rating by $55172s3.  Lasts for 1 hour.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 41191, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ReagentCount_1': 1, 'Reagent_1': 6265, 'SpellClassMask_1': 1048576, 'SpellClassSet': 5, 'SpellLevel': 36, 'SpellVisualID_1': 138, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


firebolt_3110 = spell(
    id=3110,
    name='Firebolt',
    school=School.FIRE,
    attributes=65536,
    cast_time_ms=2500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=5, points_per_level=2.4936708860759493, die_sides=3, implicit_target_a=6),
    ],
    spell_icon_id=18,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 5, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Deals $s1 Fire damage to a target.', 'EffectBonusMultiplier_1': 0.7139999866485596, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 16.0, 'SpellClassMask_1': 4096, 'SpellClassSet': 5, 'SpellLevel': 1, 'SpellVisualID_1': 67, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


torment_3716 = spell(
    id=3716,
    name='Torment',
    school=School.SHADOW,
    category=36,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=5000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.THREAT, base_points=44, points_per_level=16.142857142857142, implicit_target_a=6),
    ],
    spell_icon_id=173,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 8 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AttributesEx2': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 10, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Taunts the creature, increasing the chance that it will attack the Voidwalker.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 33554432, 'SpellClassSet': 5, 'SpellLevel': 10, 'SpellVisualID_1': 71, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


drain_mana_5138 = spell(
    id=5138,
    name='Drain Mana',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=17,
    range_yards=30.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=6, apply_aura=64, amplitude=1000),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=548,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 16388, 'AttributesEx4': 2048, 'AttributesEx5': 8192, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Drains $m1% mana each second to the caster.', 'BaseLevel': 24, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31756, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Transfers $m1% of target's maximum mana every $t1 sec from the target to the caster (up to a maximum of ${$m1*2}% of the caster's maximum mana every $t1 sec).  Lasts $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 16, 'SpellClassSet': 5, 'SpellLevel': 24, 'SpellVisualID_1': 12657, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


howl_of_terror_5484 = spell(
    id=5484,
    name='Howl of Terror',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    mechanic=Mechanic.FEAR,
    attributes=1073807360,
    category=634,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=40000,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=22, implicit_target_b=15, apply_aura=AuraType.MOD_FEAR, radius_yards=10.0),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=22, implicit_target_b=15, apply_aura=AuraType.MOD_INCREASE_SPEED, radius_yards=10.0),
    ],
    spell_icon_id=134,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 40); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 136, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Fleeing in terror.', 'BaseLevel': 40, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Howl, causing $i enemies within $a1 yds to flee in terror for $d.  Damage caused may interrupt the effect.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'MaxTargets': 5, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 664232, 'RangeIndex': 1, 'SpellClassMask_2': 8, 'SpellClassSet': 5, 'SpellLevel': 40, 'SpellVisualID_1': 4801, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


searing_pain_5676 = spell(
    id=5676,
    name='Searing Pain',
    school=School.FIRE,
    attributes=65536,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=33, points_per_level=5.061290325657014, die_sides=9, implicit_target_a=6),
    ],
    spell_icon_id=816,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 18); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 10 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 18, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Inflict searing pain on the enemy target, causing $s1 Fire damage.  Causes a high amount of threat.', 'EffectBonusMultiplier_1': 0.42899999022483826, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 256, 'SpellClassSet': 5, 'SpellLevel': 18, 'SpellVisualID_1': 945, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


unending_breath_5697 = spell(
    id=5697,
    name='Unending Breath',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=2,
    range_yards=30.0,
    duration_ms=600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=21, apply_aura=82),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=21, apply_aura=58),
    ],
    spell_icon_id=545,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Underwater Breathing.', 'BaseLevel': 16, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Allows the target to breathe underwater for $d$?s58079[ and increases swim speed by $58079s1%.][.]', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_3': 4, 'SpellClassSet': 5, 'SpellLevel': 16, 'SpellPriority': 50, 'SpellVisualID_1': 352, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


rain_of_fire_5740 = spell(
    id=5740,
    name='Rain of Fire',
    school=School.FIRE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=57,
    range_yards=30.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.PERSISTENT_AREA_AURA, base_points=41, points_per_level=7.416666666666667, implicit_target_a=28, apply_aura=AuraType.DUMMY, radius_yards=8.0),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=2000, trigger_spell=rain_of_fire_42223.id),
    ],
    spell_icon_id=547,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 7 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 268435596, 'AttributesEx2': 4194304, 'AttributesEx5': 8192, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$42223s1 Fire damage every $42223t1 seconds.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31756, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Calls down a fiery rain to burn enemies in the area of effect for ${$42223m1*4} Fire damage over $5740d.', 'EffectBonusMultiplier_1': 0.2370000034570694, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 32, 'SpellClassSet': 5, 'SpellLevel': 20, 'SpellVisualID_1': 10379, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Targets': 64},
)


fear_5782 = spell(
    id=5782,
    name='Fear',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    mechanic=Mechanic.FEAR,
    attributes=1073807360,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=12,
    range_yards=20.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_FEAR),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=6, apply_aura=AuraType.MOD_INCREASE_SPEED),
    ],
    spell_icon_id=98,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 8); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx5': 32, 'AttributesEx6': 10485760, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Feared.', 'AuraInterruptFlags': 4718592, 'BaseLevel': 8, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Strikes fear in the enemy, causing it to run in fear for up to $d.  Damage caused may interrupt the effect.  Only 1 target can be feared at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 664232, 'SpellClassMask_2': 1024, 'SpellClassSet': 5, 'SpellLevel': 8, 'SpellVisualID_1': 336, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


create_healthstone_6201 = spell(
    id=6201,
    name='Create Healthstone',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=53,
    range_yards=0.0,
    effects=[
        Effect(type=77, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=284,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1->covers-60 (anchor rank 5 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 268566528, 'AttributesEx5': 2, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 10, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Creates a Minor Healthstone that can be used to instantly restore $6262s1 health.\r\n\r\nConjured items disappear if logged out for more than 15 minutes.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ReagentCount_1': 1, 'ReagentCount_2': 1, 'Reagent_1': 6265, 'Reagent_2': -2, 'SpellClassMask_1': 1048576, 'SpellClassSet': 5, 'SpellLevel': 10, 'SpellVisualID_1': 138, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


shadow_ward_6229 = spell(
    id=6229,
    name='Shadow Ward',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    attributes=65536,
    category=56,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=30000,
    mana_cost=0,
    mana_cost_pct=12,
    range_yards=0.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=289, points_per_level=62.708333333333336, implicit_target_a=1, apply_aura=69, misc_value=32),
    ],
    spell_icon_id=207,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 32); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Absorbs Shadow damage.', 'BaseLevel': 32, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Absorbs $s1 shadow damage.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_3': 64, 'SpellClassSet': 5, 'SpellLevel': 32, 'SpellVisualID_1': 343, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


soul_fire_6353 = spell(
    id=6353,
    name='Soul Fire',
    school=School.FIRE,
    attributes=65536,
    category=631,
    cast_time_ms=6000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=9,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=622, points_per_level=21.875, die_sides=161, implicit_target_a=6),
    ],
    spell_icon_id=184,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 48); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 48, 'CastingTimeIndex': 171, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Burn the enemy's soul, causing $s1 Fire damage.", 'EffectBonusMultiplier_1': 1.149999976158142, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 6265, 'Speed': 24.0, 'SpellClassMask_2': 128, 'SpellClassSet': 5, 'SpellLevel': 48, 'SpellVisualID_1': 2253, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


soothing_kiss_6360 = spell(
    id=6360,
    name='Soothing Kiss',
    school=School.SHADOW,
    attributes=262144,
    category=82,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=4000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=10.0,
    effects=[
        Effect(type=EffectType.THREAT, base_points=-46, points_per_level=-4.137931034482759, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, mechanic=8, implicit_target_a=6, apply_aura=138),
    ],
    spell_icon_id=694,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 22); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 22, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Soothes the target, increasing the chance that it will attack something else.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 1073741824, 'SpellClassSet': 5, 'SpellLevel': 22, 'SpellVisualID_1': 2577, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


create_firestone_6366 = spell(
    id=6366,
    name='Create Firestone',
    school=School.FIRE,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=54,
    range_yards=0.0,
    effects=[
        Effect(type=24, implicit_target_a=1),
    ],
    spell_icon_id=1506,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 28); RealPointsPerLevel from rank1->covers-60 (anchor rank 4 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx5': 2, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 28, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While applied to target weapon it increases damage dealt by direct spells by 1% and spell critical strike rating by $55146s3.  Lasts for 1 hour.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 41170, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ReagentCount_1': 1, 'Reagent_1': 6265, 'SpellClassMask_1': 1048576, 'SpellClassSet': 5, 'SpellLevel': 28, 'SpellVisualID_1': 4800, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


death_coil_6789 = spell(
    id=6789,
    name='Death Coil',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    attributes=65536,
    category=633,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=120000,
    mana_cost=0,
    mana_cost_pct=23,
    range_yards=30.0,
    duration_ms=3000,
    effects=[
        Effect(type=9, base_points=243, points_per_level=14.631578947368421, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, mechanic=24, implicit_target_a=6, apply_aura=AuraType.MOD_FEAR),
    ],
    spell_icon_id=88,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 42); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Horrified.', 'BaseLevel': 42, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes the enemy target to run in horror for $d and causes $s1 Shadow damage.  The caster gains ${100*$e1}% of the damage caused in health.', 'EffectBonusMultiplier_1': 0.21400000154972076, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 3.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 24.0, 'SpellClassMask_1': 524288, 'SpellClassSet': 5, 'SpellLevel': 42, 'SpellPriority': 50, 'SpellVisualID_1': 9152, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


sacrifice_7812 = spell(
    id=7812,
    name='Sacrifice',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    attributes=536870912,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    power_type=PowerType.HEALTH,
    mana_cost=0,
    mana_cost_pct=25,
    range_yards=50000.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=304, points_per_level=125.9375, implicit_target_a=27, apply_aura=69, misc_value=127),
        Effect(type=EffectType.DUMMY, base_points=24),
    ],
    spell_icon_id=693,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 16); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 4, 'AttributesEx3': 196608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Absorbs all damage.', 'BaseLevel': 16, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Sacrifices a portion of the Voidwalker's health, giving its master a shield that will absorb $s1 damage for $d. While the shield holds, spellcasting will not be interrupted by damage.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 33554432, 'SpellClassSet': 5, 'SpellLevel': 16, 'SpellVisualID_1': 14025},
)


lash_of_pain_7814 = spell(
    id=7814,
    name='Lash of Pain',
    school=School.SHADOW,
    attributes=262160,
    category=73,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=12000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=32, points_per_level=3.4, implicit_target_a=6),
    ],
    spell_icon_id=596,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'An instant attack that lashes the target, causing $s1 Shadow damage.', 'EffectBonusMultiplier_1': 0.42899999022483826, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 8192, 'SpellClassSet': 5, 'SpellLevel': 20, 'SpellVisualID_1': 792, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


suffering_17735 = spell(
    id=17735,
    name='Suffering',
    school=School.SHADOW,
    category=84,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=120000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.THREAT, base_points=149, points_per_level=27.232142857142858, implicit_target_a=22, implicit_target_b=15, radius_yards=10.0),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=22, implicit_target_b=15, apply_aura=54, radius_yards=10.0),
    ],
    spell_icon_id=9,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 24); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 8 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 136, 'AttributesEx2': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 24, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Taunts all enemies within $a1 yards, increasing the chance that they will attack the Voidwalker.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 33554432, 'SpellClassSet': 5, 'SpellLevel': 24, 'SpellVisualID_1': 71, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


spell_lock_19244 = spell(
    id=19244,
    name='Spell Lock',
    school=School.SHADOW,
    attributes=262144,
    category=88,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=24000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.INTERRUPT_CAST, base_points=-1, mechanic=26, implicit_target_a=6),
        Effect(type=EffectType.TRIGGER_SPELL, base_points=-1, points_per_level=0.041666666666666664, mechanic=Mechanic.SILENCE, implicit_target_a=6, trigger_spell=24259),
    ],
    spell_icon_id=77,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 36); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 36, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Silences the enemy for $24259d.  If used on a casting target, it will counter the enemy's spellcast, preventing any spell from that school of magic from being cast for $d.", 'EffectBonusMultiplier_2': 0.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 5, 'SpellLevel': 36, 'SpellPriority': 50, 'SpellVisualID_1': 5282},
)


devour_magic_19505 = spell(
    id=19505,
    name='Devour Magic',
    school=School.SHADOW,
    attributes=65536,
    category=12,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=8000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.DISPEL, implicit_target_a=25, misc_value=1),
    ],
    spell_icon_id=47,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 30); RealPointsPerLevel from rank1->covers-60 (anchor rank 4 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Purges $19505s1 harmful magic $leffect:effects; from a friend or $19505s1 beneficial magic $leffect:effects; from an enemy.  If an effect is devoured, the Felhunter will be healed for $s2.', 'EffectBasePoints_2': 233, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_3': 1024, 'SpellClassSet': 5, 'SpellLevel': 30, 'SpellVisualID_1': 970, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


shadow_bolt_25307 = spell(
    id=25307,
    name='Shadow Bolt',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=17,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=481, points_per_level=3.0999999046325684, die_sides=57, implicit_target_a=6),
    ],
    spell_icon_id=213,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Sends a shadowy bolt at the enemy, causing $s1 Shadow damage.', 'EffectBonusMultiplier_1': 0.8569999933242798, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 65, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 10', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 20.0, 'SpellClassMask_1': 1, 'SpellClassSet': 5, 'SpellLevel': 60, 'SpellVisualID_1': 64, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


immolate_25309 = spell(
    id=25309,
    name='Immolate',
    school=School.FIRE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=2000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=17,
    range_yards=30.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=101, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=278, points_per_level=3.9000000953674316, implicit_target_a=6),
        Effect(type=77, die_sides=0, implicit_target_a=6),
    ],
    spell_icon_id=31,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid)',
    raw_overrides={'AttributesEx4': 1048576, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s1 Fire damage every $t1 seconds.', 'BaseLevel': 60, 'CastingTimeIndex': 5, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Burns the enemy for $s2 Fire damage and then an additional $o1 Fire damage over $d.', 'EffectBonusMultiplier_2': 0.20000000298023224, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 65, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 8', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 4, 'SpellClassSet': 5, 'SpellLevel': 60, 'SpellVisualID_1': 46, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


corruption_25311 = spell(
    id=25311,
    name='Corruption',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=14,
    range_yards=30.0,
    duration_ms=18000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=136, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
    ],
    spell_icon_id=313,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid)',
    raw_overrides={'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s1 Shadow damage every $t1 seconds.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Corrupts the target, causing $o1 Shadow damage over $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 64, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 7', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 2, 'SpellClassSet': 5, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 8629, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


seed_of_corruption_27243 = spell(
    id=27243,
    name='Seed of Corruption',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    attributes=262144,
    cast_time_ms=2000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=34,
    range_yards=30.0,
    duration_ms=18000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=173, points_per_level=7.9, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
        Effect(type=EffectType.APPLY_AURA, base_points=1043, points_per_level=47.4, implicit_target_a=6, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1932,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 70); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 3 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': "Causes $s1 Shadow damage every $t1 sec.  After taking $s2 total damage or dying, Seed of Corruption deals $27285s1 Shadow damage to the caster's enemies within $27285a1 yards.", 'AuraInterruptFlags': 1073741824, 'BaseLevel': 70, 'CastingTimeIndex': 5, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Imbeds a demon seed in the enemy target, causing $27243o1 Shadow damage over $27243d.  When the target takes $27243s2 total damage or dies, the seed will inflict $27285s1 Shadow damage to all enemies within $27285a1 yards of the target.  Only one Corruption spell per Warlock can be active on any one target.', 'EffectBonusMultiplier_1': 0.25, 'EffectBonusMultiplier_2': 0.14300000667572021, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 664232, 'Speed': 28.0, 'SpellClassMask_2': 16, 'SpellClassSet': 5, 'SpellLevel': 70, 'SpellVisualID_1': 8339, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


fel_armor_28176 = spell(
    id=28176,
    name='Fel Armor',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=28,
    range_yards=0.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=174, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=20, amplitude=5000),
        Effect(type=EffectType.APPLY_AURA, base_points=49, points_per_level=7.222222222222222, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_DONE, misc_value=126),
    ],
    spell_icon_id=2297,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 62); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 4 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases spell power by $s3 plus additional spell power equal to $s1% of your Spirit. Also regenerate $s2% of maximum health every 5 sec.', 'BaseLevel': 62, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Surrounds the caster with fel energy, increasing spell power by $s3 plus additional spell power equal to $s1% of your Spirit. In addition, you regain $s2% of your maximum health every 5 sec. Only one type of Armor spell can be active on the Warlock at any time.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 4, 'EffectSpellClassMaskB_1': 524296, 'EffectSpellClassMaskB_2': 1, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 536870912, 'SpellClassSet': 5, 'SpellLevel': 62, 'SpellVisualID_1': 7578, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


shadow_ward_28610 = spell(
    id=28610,
    name='Shadow Ward',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    attributes=65536,
    category=56,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=30000,
    mana_cost=0,
    mana_cost_pct=12,
    range_yards=0.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=874, implicit_target_a=1, apply_aura=69, misc_value=32),
    ],
    spell_icon_id=207,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Absorbs Shadow damage.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Absorbs $s1 shadow damage.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 69, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_3': 64, 'SpellClassSet': 5, 'SpellLevel': 60, 'SpellVisualID_1': 343, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


incinerate_29722 = spell(
    id=29722,
    name='Incinerate',
    school=School.FIRE,
    attributes=327680,
    cast_time_ms=2500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=14,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=402, points_per_level=11.1875, die_sides=65, implicit_target_a=6),
    ],
    spell_icon_id=2128,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 64); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 4 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 64, 'CastingTimeIndex': 19, 'CumulativeAura': 5, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Deals $s1 Fire damage to your target and an additional $/4;s1 Fire damage if the target is affected by an Immolate spell.', 'EffectBonusMultiplier_1': 0.7139999866485596, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 4, 'EffectSpellClassMaskC_1': 4, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 1, 'Speed': 20.0, 'SpellClassMask_2': 64, 'SpellClassSet': 5, 'SpellLevel': 64, 'SpellVisualID_1': 7675, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


ritual_of_souls_29893 = spell(
    id=29893,
    name='Ritual of Souls',
    school=School.SHADOW,
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
        Effect(type=50, implicit_target_a=47, misc_value=181622, radius_yards=5.0),
    ],
    spell_icon_id=2206,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 68); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 2 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131076, 'AttributesEx5': 8194, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 68, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 572430, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Begins a ritual that creates a Soulwell.  Raid members can click the Soulwell to acquire a Master Healthstone.  The Soulwell lasts for $29886d or 25 charges.  Requires the caster and 2 additional party members to complete the ritual.  In order to participate, all players must right-click the soul portal and not move until the ritual is complete.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 31, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 6265, 'SpellClassMask_2': 2147483648, 'SpellClassSet': 5, 'SpellLevel': 68, 'SpellPriority': 50, 'SpellVisualID_1': 7963, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


intercept_30151 = spell(
    id=30151,
    name='Intercept',
    school=School.NORMAL,
    attributes=537198608,
    category=1158,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=30000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=25.0,
    effects=[
        Effect(type=96, die_sides=0, implicit_target_a=6),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=6, trigger_spell=30153),
    ],
    spell_icon_id=516,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 52); RealPointsPerLevel from rank1->covers-60 (anchor rank 1 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 1536, 'AttributesEx7': 262144, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 52, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Charge an enemy, causing $30153s2 damage and stunning it for $30153d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ExcludeTargetAuraSpell': 65219, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'RangeIndex': 95, 'SpellClassSet': 5, 'SpellLevel': 52, 'SpellVisualID_1': 29, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


anguish_33698 = spell(
    id=33698,
    name='Anguish',
    school=School.SHADOW,
    category=36,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=5000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.THREAT, base_points=299, points_per_level=29.3, implicit_target_a=6),
    ],
    spell_icon_id=173,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 50); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 4 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AttributesEx2': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 50, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Taunts the creature, increasing the chance that it will attack the Felguard.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_1': 33554432, 'SpellClassSet': 5, 'SpellLevel': 50, 'SpellVisualID_1': 71, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


shadowflame_47897 = spell(
    id=47897,
    name='Shadowflame',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    category=50,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=15000,
    mana_cost=0,
    mana_cost_pct=25,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=519, points_per_level=19.0, die_sides=49, implicit_target_a=104, radius_yards=10.0),
    ],
    spell_icon_id=3317,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 75); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 2 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 136, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 75, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Targets in a cone in front of the caster take $47897s1 Shadow damage and an additional $47960o1 Fire damage over $47960d.', 'EffectBonusMultiplier_1': 0.10700000077486038, 'EffectBonusMultiplier_2': 0.10700000077486038, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'RangeIndex': 1, 'SpellClassMask_2': 65536, 'SpellClassSet': 5, 'SpellLevel': 75, 'SpellPriority': 50, 'SpellVisualID_1': 10689, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


demonic_circle_summon_48018 = spell(
    id=48018,
    name='Demonic Circle: Summon',
    school=School.SHADOW,
    attributes=2147549184,
    cast_time_ms=500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=15,
    range_yards=0.0,
    duration_ms=360000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=226, amplitude=1000),
        Effect(type=104, die_sides=0, implicit_target_a=18, misc_value=191083),
    ],
    spell_icon_id=3217,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx4': 4, 'AttributesEx5': 516, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Demonic Circle Summoned.', 'AuraInterruptFlags': 4718592, 'BaseLevel': 80, 'CastingTimeIndex': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You summon a Demonic Circle at your feet, lasting $d. You can only have one Demonic Circle active at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_3': 32, 'SpellClassSet': 5, 'SpellLevel': 80, 'SpellVisualID_1': 10677, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


demonic_circle_teleport_48020 = spell(
    id=48020,
    name='Demonic Circle: Teleport',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    mana_cost=100,
    mana_cost_pct=0,
    range_yards=40.0,
    duration_ms=1000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=11),
    ],
    spell_icon_id=3221,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268599296, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 80, 'CasterAuraSpell': 62388, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Teleports you to your Demonic Circle and removes all snare effects.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_3': 32, 'SpellClassSet': 5, 'SpellLevel': 80, 'SpellVisualID_1': 10694, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


shadow_bite_54049 = spell(
    id=54049,
    name='Shadow Bite',
    school=School.SHADOW,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=6000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=33, points_per_level=1.6842105263157894, die_sides=13, implicit_target_a=6),
    ],
    spell_icon_id=2027,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 42); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 42, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Bite the enemy, causing $s1 Shadow damage plus an additional $s3% damage for each of your damage over time effects on the target.', 'EffectBasePoints_2': -1, 'EffectBasePoints_3': 14, 'EffectBonusMultiplier_1': 0.42899999022483826, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 4194304, 'SpellClassSet': 5, 'SpellLevel': 42, 'SpellVisualID_1': 11837, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


shadowburn_17877 = spell(
    id=17877,
    name='Shadowburn',
    school=School.SHADOW,
    attributes=65536,
    category=651,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=15000,
    mana_cost=0,
    mana_cost_pct=20,
    range_yards=20.0,
    effects=[
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=6, trigger_spell=29341),
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=86, points_per_level=11.466666666666667, die_sides=13, implicit_target_a=6),
    ],
    spell_icon_id=1590,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 10 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly blasts the target for $s2 Shadow damage.  If the target dies within $29341d of Shadowburn, and yields experience or honor, the caster gains a Soul Shard.', 'EffectBonusMultiplier_2': 0.42899999022483826, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 6265, 'SpellClassMask_1': 128, 'SpellClassSet': 5, 'SpellLevel': 20, 'SpellVisualID_1': 3057, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


unstable_affliction_30108 = spell(
    id=30108,
    name='Unstable Affliction',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=15,
    range_yards=30.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=109, points_per_level=4.0, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
        Effect(type=77, die_sides=0, implicit_target_a=6),
    ],
    spell_icon_id=2039,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 50); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx4': 1048576, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s1 Shadow damage every $t1 sec.  If dispelled, will cause $*9;s1 damage to the dispeller and silence them for $31117d.', 'BaseLevel': 50, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shadow energy slowly destroys the target, causing $o1 damage over $d.  In addition, if the Unstable Affliction is dispelled it will cause $*9;s1 damage to the dispeller and silence them for $31117d. Only one Unstable Affliction or Immolate per Warlock can be active on any one target.', 'EffectBonusMultiplier_1': 0.20000000298023224, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 256, 'SpellClassSet': 5, 'SpellLevel': 50, 'SpellPriority': 50, 'SpellVisualID_1': 8141, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


shadowfury_30283 = spell(
    id=30283,
    name='Shadowfury',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    attributes=65536,
    category=250,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=20000,
    mana_cost=0,
    mana_cost_pct=27,
    range_yards=30.0,
    duration_ms=3000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=342, points_per_level=20.833333333333332, die_sides=65, implicit_target_a=16, radius_yards=8.0),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, mechanic=Mechanic.STUN, implicit_target_a=16, apply_aura=AuraType.MOD_STUN, radius_yards=8.0),
    ],
    spell_icon_id=1988,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 50); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 136, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Stunned.', 'BaseLevel': 50, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shadowfury is unleashed, causing $s1 Shadow damage and stunning all enemies within $a1 yds for $d.', 'EffectBonusMultiplier_1': 0.19300000369548798, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 4096, 'SpellClassSet': 5, 'SpellLevel': 50, 'SpellPriority': 50, 'SpellVisualID_1': 7732, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 500, 'Targets': 64},
)


haunt_48181 = spell(
    id=48181,
    name='Haunt',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    category=1222,
    cast_time_ms=1500,
    cooldown_ms=8000,
    category_cooldown_ms=8000,
    mana_cost=0,
    mana_cost_pct=12,
    range_yards=30.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=404, points_per_level=12.0, die_sides=69, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=6, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=6, apply_aura=271),
    ],
    spell_icon_id=3172,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 60); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 4 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx3': 67108992, 'AttributesEx5': 32, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage taken from Shadow damage-over-time effects increased by $s3%.', 'BaseLevel': 60, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You send a ghostly soul into the target, dealing $s1 Shadow damage and increasing all damage done by your Shadow damage-over-time effects on the target by $s3% for $d. When the Haunt spell ends or is dispelled, the soul returns to you, healing you for $s2% of the damage it did to the target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskC_1': 17418, 'EffectSpellClassMaskC_2': 273, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 20.0, 'SpellClassMask_2': 262144, 'SpellClassSet': 5, 'SpellLevel': 60, 'SpellVisualID_1': 10731, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


chaos_bolt_50796 = spell(
    id=50796,
    name='Chaos Bolt',
    school=School.FIRE,
    attributes=65536,
    category=1225,
    cast_time_ms=2500,
    cooldown_ms=0,
    category_cooldown_ms=12000,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=836, points_per_level=29.6, die_sides=225, implicit_target_a=6),
    ],
    spell_icon_id=3178,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 60); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 4 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx3': 262144, 'AttributesEx4': 2048, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 19, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Sends a bolt of chaotic fire at the enemy, dealing $s1 Fire damage. Chaos Bolt cannot be resisted, and pierces through all absorption effects.', 'EffectBonusMultiplier_1': 0.7139999866485596, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 20.0, 'SpellClassMask_2': 131072, 'SpellClassSet': 5, 'SpellLevel': 60, 'SpellVisualID_1': 11240, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


conflagrate_17962 = spell(
    id=17962,
    name='Conflagrate',
    school=School.FIRE,
    attributes=65536,
    category=672,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    mana_cost=0,
    mana_cost_pct=16,
    range_yards=30.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=59, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=2000),
    ],
    spell_icon_id=12,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Fire damage every $t2 seconds.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': '$?s56235[Causes][Consumes] an Immolate or Shadowflame effect on the enemy target to instantly deal damage equal to $s2% of your Immolate or Shadowflame, and causes an additional $s3% damage over $d.', 'EffectBasePoints_3': 39, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 8388608, 'SpellClassSet': 5, 'SpellLevel': 1, 'SpellVisualID_1': 5199, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetAuraState': 14},
)


curse_of_exhaustion_18223 = spell(
    id=18223,
    name='Curse of Exhaustion',
    school=School.SHADOW,
    dispel=DispelType.CURSE,
    mechanic=Mechanic.SNARE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=30.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=6, apply_aura=AuraType.MOD_DECREASE_SPEED),
    ],
    spell_icon_id=228,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement speed slowed by $s1%.', 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces the target's movement speed by $s1% for $d.  Only one Curse per Warlock can be active on any one target.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 4194304, 'SpellClassSet': 5, 'SpellVisualID_1': 8785, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


fel_domination_18708 = spell(
    id=18708,
    name='Fel Domination',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-5501, implicit_target_a=1, apply_aura=107, misc_value=10),
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=195,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Imp, Voidwalker, Succubus, Felhunter and Felguard casting time reduced by $/1000;S1 sec.  Mana cost reduced by $s2%.', 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your next Imp, Voidwalker, Succubus, Felhunter or Felguard Summon spell has its casting time reduced by $/1000;S1 sec and its Mana cost reduced by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 536870912, 'EffectSpellClassMaskB_1': 536870912, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassMask_3': 128, 'SpellClassSet': 5, 'SpellVisualID_1': 4600},
)


soul_link_19028 = spell(
    id=19028,
    name='Soul Link',
    school=School.SHADOW,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=16,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.DUMMY, implicit_target_a=5),
    ],
    spell_icon_id=173,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 4, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When active, $25228s1% of all damage taken by the caster is taken by your Imp, Voidwalker, Succubus, Felhunter, Felguard, or enslaved demon instead.  That damage cannot be prevented. Lasts as long as the demon is active and controlled.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_3': 64, 'SpellClassSet': 5, 'SpellLevel': 20, 'SpellVisualID_1': 969, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetCreatureType': 4},
)


summon_felguard_30146 = spell(
    id=30146,
    name='Summon Felguard',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=10000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=80,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=56, implicit_target_a=32, misc_value=17252),
    ],
    spell_icon_id=1983,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131073, 'AttributesEx5': 2, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 50, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Felguard under the command of the Warlock.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Summon', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ReagentCount_1': 1, 'Reagent_1': 6265, 'SpellClassMask_1': 536870912, 'SpellClassSet': 5, 'SpellLevel': 50, 'SpellVisualID_1': 8360, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


demonic_empowerment_47193 = spell(
    id=47193,
    name='Demonic Empowerment',
    school=School.SHADOW,
    attributes=537200640,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=100.0,
    effects=[
        Effect(type=77, base_points=-1, implicit_target_a=5),
    ],
    spell_icon_id=3174,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 4, 'AttributesEx3': 1073741824, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Empowered.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Grants the Warlock's summoned demon Empowerment.\r\n\r\nImp - Increases the Imp's spell critical strike chance by $54444s1% for $54444d.\r\n\r\nVoidwalker - Increases the Voidwalker's health by $54443s2%, and its threat generated from spells and attacks by $54443s2% for $54443d.\r\n\r\nSuccubus - Instantly vanishes, causing the Succubus to go into an improved Invisibility state. The vanish effect removes all stuns, snares and movement impairing effects from the Succubus.\r\n\r\nFelhunter - Dispels all magical effects from the Felhunter.\r\n\r\nFelguard - Increases the Felguard's attack speed by $54508s1% and breaks all stun, snare and movement impairing effects and makes your Felguard immune to them for $54508d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'SpellClassMask_3': 4160, 'SpellClassSet': 5, 'SpellLevel': 30, 'SpellVisualID_1': 13422, 'TargetCreatureType': 4},
)
