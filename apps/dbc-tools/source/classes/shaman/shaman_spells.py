"""
Shaman - player-castable spells (real cast_time_ms/cooldown_ms, not marked passive).

Split from a single source/classes/shaman.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .shaman_...` below) resolve.
"""

from lib.dsl import AuraType, DispelType, Effect, EffectType, Mechanic, School
from lib.dsl.registry import spell


water_breathing_131 = spell(
    id=131,
    name='Water Breathing',
    school=School.NATURE,
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
    ],
    spell_icon_id=545,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Able to breathe underwater.', 'BaseLevel': 22, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Allows the target to breathe underwater for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17057, 'SpellClassMask_2': 268437504, 'SpellClassSet': 11, 'SpellLevel': 22, 'SpellPriority': 50, 'SpellVisualID_1': 371, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


healing_wave_331 = spell(
    id=331,
    name='Healing Wave',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=25,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=33, points_per_level=37.9746835443038, die_sides=11, implicit_target_a=45),
    ],
    spell_icon_id=13,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 14 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals a friendly target for $s1.', 'EffectBonusMultiplier_1': 1.6109999418258667, 'EffectChainAmplitude_1': 0.20000000298023224, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 64, 'SpellClassSet': 11, 'SpellLevel': 1, 'SpellVisualID_1': 58, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


purge_370 = spell(
    id=370,
    name='Purge',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.DISPEL, points_per_level=0.020833333333333332, implicit_target_a=6, misc_value=1),
    ],
    spell_icon_id=47,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 12); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 12, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Purges the enemy target, removing $m1 beneficial magic $leffect:effects;.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 2048, 'SpellClassSet': 11, 'SpellLevel': 12, 'SpellVisualID_1': 214, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


lightning_bolt_403 = spell(
    id=403,
    name='Lightning Bolt',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=2500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=12, points_per_level=8.936708860759493, die_sides=3, implicit_target_a=6),
    ],
    spell_icon_id=62,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 14 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Casts a bolt of lightning at the target for $s1 Nature damage.', 'EffectBonusMultiplier_1': 0.7139999866485596, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 20.0, 'SpellClassMask_1': 1, 'SpellClassSet': 11, 'SpellLevel': 1, 'SpellVisualID_1': 173, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


chain_lightning_421 = spell(
    id=421,
    name='Chain Lightning',
    school=School.NATURE,
    attributes=65536,
    category=85,
    cast_time_ms=2000,
    cooldown_ms=0,
    category_cooldown_ms=6000,
    mana_cost=0,
    mana_cost_pct=26,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=190, points_per_level=16.291666666666668, die_sides=27, implicit_target_a=6, chain_targets=3),
    ],
    spell_icon_id=165,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 32); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 8 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 32, 'CastingTimeIndex': 5, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Hurls a lightning bolt at the enemy, dealing $s1 Nature damage and then jumping to additional nearby enemies.  Each jump reduces the damage by 30%.  Affects $x1 total targets.', 'EffectBonusMultiplier_1': 0.5709999799728394, 'EffectChainAmplitude_1': 0.699999988079071, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 2, 'SpellClassSet': 11, 'SpellLevel': 32, 'SpellVisualID_1': 36, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


cure_toxins_526 = spell(
    id=526,
    name='Cure Toxins',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.DISPEL, implicit_target_a=21, misc_value=4),
        Effect(type=EffectType.DISPEL, implicit_target_a=21, misc_value=3),
    ],
    spell_icon_id=194,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 16, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Cures $s1 poison $leffect:effects; and $s1 disease $leffect:effects; on a friendly target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 8, 'SpellClassSet': 11, 'SpellLevel': 16, 'SpellVisualID_1': 187, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


water_walking_546 = spell(
    id=546,
    name='Water Walking',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=30.0,
    duration_ms=600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=21, apply_aura=104),
    ],
    spell_icon_id=101,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Allows walking over water.', 'AuraInterruptFlags': 2, 'BaseLevel': 28, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Allows the friendly target to walk across water for $d.  Any damage will cancel the effect.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17058, 'SpellClassMask_2': 536872960, 'SpellClassSet': 11, 'SpellLevel': 28, 'SpellVisualID_1': 4483, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


astral_recall_556 = spell(
    id=556,
    name='Astral Recall',
    school=School.NATURE,
    attributes=268500992,
    category=511,
    cast_time_ms=10000,
    cooldown_ms=0,
    category_cooldown_ms=900000,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=0.0,
    effects=[
        Effect(type=5, base_points=-1, implicit_target_a=1, implicit_target_b=9),
    ],
    spell_icon_id=458,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 30, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Yanks the caster through the twisting nether back to $z.  Speak to an Innkeeper in a different place to change your home location.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 1073741824, 'SpellClassSet': 11, 'SpellLevel': 30, 'SpellVisualID_1': 220, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


chain_heal_1064 = spell(
    id=1064,
    name='Chain Heal',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=2500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=19,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=319, points_per_level=18.375, die_sides=49, implicit_target_a=45, chain_targets=3),
    ],
    spell_icon_id=963,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 40); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 7 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 40, 'CastingTimeIndex': 19, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals the friendly target for $s1, then jumps to heal additional nearby targets.  If cast on a party member, the heal will only jump to other party members.  Each jump reduces the effectiveness of the heal by 40%.  Heals $x1 total targets.', 'EffectBonusMultiplier_1': 1.343000054359436, 'EffectChainAmplitude_1': 0.6000000238418579, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 256, 'SpellClassSet': 11, 'SpellLevel': 40, 'SpellVisualID_1': 3659, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


fire_nova_1535 = spell(
    id=1535,
    name='Fire Nova',
    school=School.FIRE,
    attributes=65536,
    category=35,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    mana_cost=0,
    mana_cost_pct=22,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=-1, points_per_level=0.07352941176470588, implicit_target_a=1),
    ],
    spell_icon_id=33,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 12); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 12, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Causes the shaman's active Fire totem to emit a wave of flames, inflicting $8349s1 Fire damage to enemies within $8349a1 yards of the totem.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 134217728, 'SpellClassSet': 11, 'SpellLevel': 12, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


ancestral_spirit_2008 = spell(
    id=2008,
    name='Ancestral Spirit',
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
    spell_icon_id=149,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 12); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 7 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 12, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Returns the spirit to the body, restoring a dead target to life with $s1 health and $q1 mana.  Cannot be cast when in combat.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 11, 'SpellLevel': 12, 'SpellPriority': 50, 'SpellVisualID_1': 344, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Targets': 32768},
)


earth_elemental_totem_2062 = spell(
    id=2062,
    name='Earth Elemental Totem',
    school=School.NORMAL,
    attributes=65536,
    category=23,
    cast_time_ms=0,
    cooldown_ms=600000,
    category_cooldown_ms=120000,
    mana_cost=0,
    mana_cost_pct=24,
    range_yards=0.0,
    duration_ms=120000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=7399, implicit_target_a=22, implicit_target_b=41, misc_value=15430, radius_yards=5.0),
    ],
    spell_icon_id=2289,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx4': 65536, 'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 66, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summon an elemental totem that calls forth a greater earth elemental to protect the caster and $ghis:her; allies.  Lasts $d.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 81, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 2, 'SpellClassMask_1': 536870912, 'SpellClassMask_2': 4194304, 'SpellClassSet': 11, 'SpellLevel': 66, 'SpellVisualID_1': 319, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


earthbind_totem_2484 = spell(
    id=2484,
    name='Earthbind Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=15000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=0.0,
    duration_ms=45000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=41, misc_value=2630),
    ],
    spell_icon_id=686,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 6, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons an Earthbind Totem with $s1 health at the feet of the caster for $d that slows the movement speed of enemies within $3600a1 yards.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 81, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 2, 'SpellClassMask_1': 536870912, 'SpellClassMask_3': 32, 'SpellClassSet': 11, 'SpellLevel': 6, 'SpellVisualID_1': 264, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


ghost_wolf_2645 = spell(
    id=2645,
    name='Ghost Wolf',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=98304,
    cast_time_ms=2000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=36, misc_value=16),
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=AuraType.MOD_INCREASE_SPEED),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=20, amplitude=5000),
    ],
    spell_icon_id=67,
    notes='pulled from existing data',
    raw_overrides={'ActiveIconID': 122, 'AttributesEx': 132096, 'AttributesEx2': 2, 'AttributesEx4': 64, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases movement speed by $s2%$?s59289[ and regenerates $59289s1% of your maximum health every 5 sec][].\r\nEffects that reduce movement speed may not bring you below your normal movement speed.', 'BaseLevel': 16, 'CastingTimeIndex': 5, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Turns the Shaman into a Ghost Wolf, increasing speed by $s2%$?s59289[ and regenerating $59289s1% of your maximum health every 5 sec][]. As a Ghost Wolf, the Shaman is less hindered by effects that would reduce movement speed. Only useable outdoors.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EffectMultipleValue_2': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 2048, 'SpellClassSet': 11, 'SpellLevel': 16, 'SpellPriority': 50, 'SpellVisualID_1': 311, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


bloodlust_2825 = spell(
    id=2825,
    name='Bloodlust',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=300000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=26,
    range_yards=0.0,
    duration_ms=40000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=56, apply_aura=192, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=56, apply_aura=61, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=56, apply_aura=65, radius_yards=100.0),
    ],
    spell_icon_id=38,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx6': 67108864, 'AttributesEx7': 256, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Melee, ranged, and spell casting speed increased by $s1%.', 'BaseLevel': 70, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases melee, ranged, and spell casting speed by $s1% for all party and raid members.  Lasts $d.\r\n\r\nAfter the completion of this effect, those affected will become Sated and unable to benefit from Bloodlust again for $57724d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 64, 'SpellClassSet': 11, 'SpellLevel': 70, 'SpellVisualID_1': 7870, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


fire_elemental_totem_2894 = spell(
    id=2894,
    name='Fire Elemental Totem',
    school=School.NORMAL,
    attributes=327680,
    category=23,
    cast_time_ms=0,
    cooldown_ms=600000,
    category_cooldown_ms=120000,
    mana_cost=0,
    mana_cost_pct=23,
    range_yards=0.0,
    duration_ms=120000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=3887, implicit_target_a=22, implicit_target_b=44, misc_value=15439, radius_yards=5.0),
    ],
    spell_icon_id=2290,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx4': 65536, 'AttributesEx6': 2147483648, 'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 68, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Summons an elemental totem that calls forth a greater fire elemental to rain destruction on the caster's enemies.  Lasts $d.", 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 63, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 4, 'SpellClassMask_1': 536870912, 'SpellClassMask_2': 8388608, 'SpellClassSet': 11, 'SpellLevel': 68, 'SpellVisualID_1': 221, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


searing_totem_3599 = spell(
    id=3599,
    name='Searing Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=0.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=44, misc_value=2523),
    ],
    spell_icon_id=680,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1->covers-60 (anchor rank 6 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 10, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Searing Totem with $s1 health at your feet for $d that repeatedly attacks an enemy within $3606r1 yards for $3606s1 Fire damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 63, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 4, 'SpellClassMask_1': 16, 'SpellClassSet': 11, 'SpellLevel': 10, 'SpellVisualID_1': 221, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


attack_3606 = spell(
    id=3606,
    name='Attack',
    school=School.FIRE,
    cast_time_ms=2200,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=20.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=8, points_per_level=1.1571428571428573, die_sides=3, implicit_target_a=6),
    ],
    spell_icon_id=680,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 10 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 10, 'CastingTimeIndex': 24, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Deals Fire damage to the target.', 'EffectBonusMultiplier_1': 0.16699999570846558, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 19.0, 'SpellClassMask_1': 1073741824, 'SpellClassSet': 11, 'SpellLevel': 10, 'SpellVisualID_1': 67},
)


wrath_of_air_totem_3738 = spell(
    id=3738,
    name='Wrath of Air Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=11,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=43, misc_value=15447),
    ],
    spell_icon_id=340,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 64, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Wrath of Air Totem with $s1 health at the feet of the caster.  The totem provides $2895s1% spell haste to all party and raid members within $2895a1 yards.  Lasts $d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 83, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 3, 'SpellClassMask_1': 536870912, 'SpellClassSet': 11, 'SpellLevel': 64, 'SpellVisualID_1': 319, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


healing_stream_totem_5394 = spell(
    id=5394,
    name='Healing Stream Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=42, misc_value=3527),
    ],
    spell_icon_id=1647,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->covers-60 (anchor rank 5 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Healing Stream Totem with $s1 health at the feet of the caster for $d that heals group members within $52041a1 yards for $5672s1 every $5672t1 seconds.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 82, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 5, 'SpellClassMask_1': 524288, 'SpellClassSet': 11, 'SpellLevel': 20, 'SpellVisualID_1': 319, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


mana_spring_totem_5675 = spell(
    id=5675,
    name='Mana Spring Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=4,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=42, misc_value=3573),
    ],
    spell_icon_id=338,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 26); RealPointsPerLevel from rank1->covers-60 (anchor rank 4 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 26, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Mana Spring Totem with $s1 health at the feet of the caster for $d that restores $5677s1 mana every 5 seconds to all party and raid members within $52031a1 yards.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 82, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 5, 'SpellClassMask_1': 524288, 'SpellClassSet': 11, 'SpellLevel': 26, 'SpellVisualID_1': 364, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


stoneclaw_totem_5730 = spell(
    id=5730,
    name='Stoneclaw Totem',
    school=School.NORMAL,
    attributes=65536,
    category=45,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=30000,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=49, points_per_level=21.88888888888889, implicit_target_a=41, misc_value=3579),
    ],
    spell_icon_id=689,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 8); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 10 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Taunting creatures.', 'BaseLevel': 8, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Stoneclaw Totem with $s1 health at the feet of the caster for $d that taunts creatures within $5729a1 yards to attack it.  Enemies attacking the Stoneclaw Totem have a $5728h% chance to be stunned for $39796d. Stoneclaw totem also protects all your totems, causing them to absorb $55328s1 damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 81, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 2, 'SpellClassMask_1': 8, 'SpellClassSet': 11, 'SpellLevel': 8, 'SpellVisualID_1': 362, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


sentry_totem_6495 = spell(
    id=6495,
    name='Sentry Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=2,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=99, implicit_target_a=43, misc_value=3968, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=195,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 139264, 'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Allows vision through Sentry Totem.  Right-Click on buff to switch back and forth between totem sight and shaman sight.', 'BaseLevel': 34, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons an immobile Sentry Totem with $s1 health at your feet for $d that allows vision of nearby area and warns of enemies that attack it.  Right-Click on buff to switch back and forth between totem sight and shaman sight.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 83, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 3, 'SpellClassMask_1': 536870912, 'SpellClassSet': 11, 'SpellLevel': 34, 'SpellVisualID_1': 368, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


lesser_healing_wave_8004 = spell(
    id=8004,
    name='Lesser Healing Wave',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=15,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=161, points_per_level=24.366666666666667, die_sides=25, implicit_target_a=21),
    ],
    spell_icon_id=964,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals a friendly target for $s1.', 'EffectBonusMultiplier_1': 0.8069999814033508, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 128, 'SpellClassSet': 11, 'SpellLevel': 20, 'SpellVisualID_1': 58, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


rockbiter_weapon_8017 = spell(
    id=8017,
    name='Rockbiter Weapon',
    school=School.NATURE,
    attributes=328192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    effects=[
        None,
        Effect(type=54, base_points=1),
    ],
    spell_icon_id=688,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 4 @ level 32); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131088, 'AttributesEx2': 8, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Imbue the Shaman's weapon, increasing its damage per second by $s2.  Lasts 30 minutes.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 4194304, 'SpellClassSet': 11, 'SpellLevel': 1, 'SpellVisualID_1': 8693, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Targets': 16},
)


flametongue_weapon_8024 = spell(
    id=8024,
    name='Flametongue Weapon',
    school=School.FIRE,
    attributes=328192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=0.0,
    effects=[
        Effect(type=54, base_points=1799, misc_value=5),
    ],
    spell_icon_id=679,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1->covers-60 (anchor rank 6 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 8, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 10, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Imbue the Shaman's weapon with fire, increasing total spell damage by $10400s2$?s55451[ and increasing spell critical strike chance by $55451s1%.][.] Each hit causes $/77;8026m1 to $/25;8026M1 additional Fire damage, based on the speed of the weapon.  Slower weapons cause more fire damage per swing.  Lasts 30 minutes.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 2048, 'SpellClassSet': 11, 'SpellLevel': 10, 'SpellVisualID_1': 8722, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Targets': 16},
)


frostbrand_weapon_8033 = spell(
    id=8033,
    name='Frostbrand Weapon',
    school=School.FROST,
    attributes=328192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=0.0,
    effects=[
        Effect(type=54, base_points=1799, misc_value=2),
    ],
    spell_icon_id=681,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->covers-60 (anchor rank 5 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 8, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Imbue the Shaman's weapon with frost.  Each hit has a chance of causing $8034s2 additional Frost damage and slowing the target's movement speed by $8034s1% for $8034d.  Lasts 30 minutes.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 2048, 'SpellClassSet': 11, 'SpellLevel': 20, 'SpellVisualID_1': 8721, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Targets': 16},
)


earth_shock_8042 = spell(
    id=8042,
    name='Earth Shock',
    school=School.NATURE,
    attributes=327680,
    category=19,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=6000,
    mana_cost=0,
    mana_cost_pct=18,
    range_yards=25.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, mechanic=8, implicit_target_a=6, apply_aura=138),
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=16, points_per_level=11.013157894736842, die_sides=3, implicit_target_a=6),
    ],
    spell_icon_id=687,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 4); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 10 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Time between attacks increased by $s1%.', 'BaseLevel': 4, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly shocks the target with concussive force, causing $s2 Nature damage and reducing melee attack speed by $s1% for $d.', 'EffectBonusMultiplier_2': 0.38600000739097595, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 1048576, 'SpellClassSet': 11, 'SpellLevel': 4, 'SpellVisualID_1': 3444, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


flame_shock_8050 = spell(
    id=8050,
    name='Flame Shock',
    school=School.FIRE,
    dispel=DispelType.MAGIC,
    attributes=327680,
    category=19,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=6000,
    mana_cost=0,
    mana_cost_pct=17,
    range_yards=25.0,
    duration_ms=18000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=20, points_per_level=6.8428571428571425, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=6, points_per_level=1.8857142857142857, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
    ],
    spell_icon_id=678,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx5': 8192, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s2 Fire damage every $t2 seconds.', 'BaseLevel': 10, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Instantly sears the target with fire, causing $s1 Fire damage immediately and $o2 Fire damage over $d. This periodic damage may critically strike and will occur more rapidly based on the caster's spell haste.", 'EffectBonusMultiplier_1': 0.21400000154972076, 'EffectBonusMultiplier_2': 0.10000000149011612, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 268435456, 'SpellClassSet': 11, 'SpellLevel': 10, 'SpellVisualID_1': 3445, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


frost_shock_8056 = spell(
    id=8056,
    name='Frost Shock',
    school=School.FROST,
    dispel=DispelType.MAGIC,
    attributes=327680,
    category=19,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=6000,
    mana_cost=0,
    mana_cost_pct=18,
    range_yards=25.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-51, mechanic=Mechanic.SNARE, implicit_target_a=6, apply_aura=AuraType.MOD_DECREASE_SPEED),
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=88, points_per_level=12.05, die_sides=7, implicit_target_a=6),
    ],
    spell_icon_id=976,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 7 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement slowed by $s1%.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly shocks the target with frost, causing $s2 Frost damage and slowing movement speed by $s1%.  Lasts $d.  Causes a high amount of threat.', 'EffectBonusMultiplier_2': 0.38600000739097595, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 11, 'SpellLevel': 20, 'SpellVisualID_1': 144, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


stoneskin_totem_8071 = spell(
    id=8071,
    name='Stoneskin Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=41, misc_value=5873),
    ],
    spell_icon_id=690,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 4); RealPointsPerLevel from rank1->covers-60 (anchor rank 6 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 4, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Stoneskin Totem with $s1 health at the feet of the caster.  The totem protects party and raid members within $8072a1 yards, increasing armor by $8072s1.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 81, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 2, 'SpellClassMask_1': 536870912, 'SpellClassSet': 11, 'SpellLevel': 4, 'SpellVisualID_1': 319, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


strength_of_earth_totem_8075 = spell(
    id=8075,
    name='Strength of Earth Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=41, misc_value=5874),
    ],
    spell_icon_id=691,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1->covers-60 (anchor rank 5 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 10, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Strength of Earth Totem with $s1 health at the feet of the caster.  The totem increases the strength and agility of all party and raid members within $8076a1 yards by $8076s2.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 81, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 2, 'SpellClassMask_1': 536870912, 'SpellClassSet': 11, 'SpellLevel': 10, 'SpellVisualID_1': 319, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


tremor_totem_8143 = spell(
    id=8143,
    name='Tremor Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=2,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=41, misc_value=5913),
    ],
    spell_icon_id=1676,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 18, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Tremor Totem with $s1 health at the feet of the caster that shakes the ground around it, removing Fear, Charm and Sleep effects from party members within $8146a1 yards.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 81, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 2, 'SpellClassMask_1': 536870912, 'SpellClassSet': 11, 'SpellLevel': 18, 'SpellVisualID_1': 319, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


cleansing_totem_8170 = spell(
    id=8170,
    name='Cleansing Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=42, misc_value=5924),
    ],
    spell_icon_id=1673,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 38, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Cleansing Totem with $s1 health at the feet of the caster that attempts to remove 1 disease and 1 poison effect from party members within $8171a1 yards every $8172t1 seconds.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 82, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 5, 'SpellClassMask_1': 536870912, 'SpellClassSet': 11, 'SpellLevel': 38, 'SpellVisualID_1': 319, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


grounding_totem_8177 = spell(
    id=8177,
    name='Grounding Totem',
    school=School.NORMAL,
    attributes=65536,
    category=230,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=15000,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=0.0,
    duration_ms=45000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=43, misc_value=5925),
    ],
    spell_icon_id=1677,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 1073741824, 'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Grounding Totem with $s1 health at the feet of the caster that will redirect one harmful spell cast on a nearby party member to itself, destroying the totem.  Will not redirect area of effect spells.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 83, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 3, 'SpellClassMask_1': 537133056, 'SpellClassSet': 11, 'SpellLevel': 30, 'SpellVisualID_1': 319, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


frost_resistance_totem_8181 = spell(
    id=8181,
    name='Frost Resistance Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=44, misc_value=5926),
    ],
    spell_icon_id=1713,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 24); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 24, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Summons a Frost Resistance Totem with $s1 health at the feet of the caster for $d.  The totem increases party and raid members' frost resistance by $8182s1, if within $8182a1 yards.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 63, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 4, 'SpellClassMask_1': 536870912, 'SpellClassSet': 11, 'SpellLevel': 24, 'SpellVisualID_1': 319, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


fire_resistance_totem_8184 = spell(
    id=8184,
    name='Fire Resistance Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=42, misc_value=5927),
    ],
    spell_icon_id=1712,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 28); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 28, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Fire Resistance Totem with $s1 health at the feet of the caster for $d that increases the fire resistance of party and raid members within $8185a1 yards by $8185s1.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 82, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 5, 'SpellClassMask_1': 536870912, 'SpellClassSet': 11, 'SpellLevel': 28, 'SpellVisualID_1': 319, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


magma_totem_8190 = spell(
    id=8190,
    name='Magma Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=27,
    range_yards=0.0,
    duration_ms=21000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=44, misc_value=5929),
    ],
    spell_icon_id=37,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 26); RealPointsPerLevel from rank1->covers-60 (anchor rank 4 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 26, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Magma Totem with $s1 health at the feet of the caster for ${$d-1} sec that causes $8187s1 Fire damage to creatures within $8187a1 yards every $8188t1 seconds.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 63, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 4, 'SpellClassMask_1': 4096, 'SpellClassSet': 11, 'SpellLevel': 26, 'SpellVisualID_1': 369, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


flametongue_totem_8227 = spell(
    id=8227,
    name='Flametongue Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=11,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=44, misc_value=5950),
    ],
    spell_icon_id=72,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 28); RealPointsPerLevel from rank1->covers-60 (anchor rank 4 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 28, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Flametongue Totem with $s1 health at the feet of the caster.  Party and raid members within $52109a1 yards of the totem have their spell damage and healing increased by up to $52109s1.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 63, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 4, 'SpellClassMask_1': 536870912, 'SpellClassSet': 11, 'SpellLevel': 28, 'SpellVisualID_1': 221, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


windfury_weapon_8232 = spell(
    id=8232,
    name='Windfury Weapon',
    school=School.NATURE,
    attributes=328192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=0.0,
    effects=[
        Effect(type=54, base_points=1799, misc_value=283),
    ],
    spell_icon_id=220,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 30); RealPointsPerLevel from rank1->covers-60 (anchor rank 4 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 8, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Imbue the Shaman's weapon with wind.  Each hit has a 20% chance of dealing additional damage equal to two extra attacks with $s2 extra attack power.  Lasts 30 minutes.", 'EffectBasePoints_2': 45, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 2048, 'SpellClassSet': 11, 'SpellLevel': 30, 'SpellVisualID_1': 8723, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Targets': 16},
)


windfury_totem_8512 = spell(
    id=8512,
    name='Windfury Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=11,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=43, misc_value=6112),
    ],
    spell_icon_id=1397,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases melee haste by $8515s1%.', 'BaseLevel': 32, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Windfury Totem with $s1 health at the feet of the caster.  The totem provides $8515s1% melee haste to all party and raid members within $8515a1 yards.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 83, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 3, 'SpellClassMask_1': 536870912, 'SpellClassSet': 11, 'SpellLevel': 32, 'SpellVisualID_1': 221, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


nature_resistance_totem_10595 = spell(
    id=10595,
    name='Nature Resistance Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=43, misc_value=7467),
    ],
    spell_icon_id=1675,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 30); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Nature Resistance Totem with $s1 health at the feet of the caster for $d that increases the nature resistance of party and raid members within $10596a1 yards by $10596s1.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 83, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 3, 'SpellClassMask_1': 536870912, 'SpellClassSet': 11, 'SpellLevel': 30, 'SpellVisualID_1': 319, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


healing_wave_25357 = spell(
    id=25357,
    name='Healing Wave',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=25,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=1619, points_per_level=5.5, die_sides=231, implicit_target_a=45),
    ],
    spell_icon_id=13,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals a friendly target for $s1.', 'EffectBonusMultiplier_1': 1.6109999418258667, 'EffectChainAmplitude_1': 0.20000000298023224, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 65, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 10', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 64, 'SpellClassSet': 11, 'SpellLevel': 60, 'SpellVisualID_1': 58, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


strength_of_earth_totem_25361 = spell(
    id=25361,
    name='Strength of Earth Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=41, misc_value=15464),
    ],
    spell_icon_id=691,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid)',
    raw_overrides={'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Strength of Earth Totem with $s1 health at the feet of the caster.  The totem increases the strength and agility of all party and raid members within $25362a1 yards by $25362s2.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 81, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 2, 'SpellClassMask_1': 536870912, 'SpellClassSet': 11, 'SpellLevel': 60, 'SpellVisualID_1': 319, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


flame_shock_29228 = spell(
    id=29228,
    name='Flame Shock',
    school=School.FIRE,
    dispel=DispelType.MAGIC,
    attributes=327680,
    category=19,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=6000,
    mana_cost=0,
    mana_cost_pct=17,
    range_yards=25.0,
    duration_ms=18000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=308, points_per_level=3.5, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=85, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
    ],
    spell_icon_id=678,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid)',
    raw_overrides={'AttributesEx5': 8192, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s2 Fire damage every $t2 seconds.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Instantly sears the target with fire, causing $s1 Fire damage immediately and $o2 Fire damage over $d. This periodic damage may critically strike and will occur more rapidly based on the caster's spell haste.", 'EffectBonusMultiplier_1': 0.21400000154972076, 'EffectBonusMultiplier_2': 0.10000000149011612, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 67, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 6', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 268435456, 'SpellClassSet': 11, 'SpellLevel': 60, 'SpellVisualID_1': 3445, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


heroism_32182 = spell(
    id=32182,
    name='Heroism',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=300000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=26,
    range_yards=0.0,
    duration_ms=40000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=56, apply_aura=192, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=56, apply_aura=61, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=56, apply_aura=65, radius_yards=100.0),
    ],
    spell_icon_id=2288,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx6': 67108864, 'AttributesEx7': 512, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Melee, ranged, and spell casting speed increased by $s1%.', 'BaseLevel': 70, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases melee, ranged, and spell casting speed by $s1% for all party and raid members.  Lasts $d.\r\n\r\nAfter the completion of this effect, those affected will become Exhausted and unable to benefit from Heroism again for $57723d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 74, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 64, 'SpellClassSet': 11, 'SpellLevel': 70, 'SpellVisualID_1': 7922, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


lava_burst_51505 = spell(
    id=51505,
    name='Lava Burst',
    school=School.FIRE,
    attributes=65536,
    category=1224,
    cast_time_ms=2000,
    cooldown_ms=0,
    category_cooldown_ms=8000,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=1011, points_per_level=36.0, die_sides=279, implicit_target_a=6),
    ],
    spell_icon_id=3064,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 75); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 2 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx3': 1048576, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 75, 'CastingTimeIndex': 5, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You hurl molten lava at the target, dealing $s1 Fire damage. If your Flame Shock is on the target, Lava Burst will deal a critical strike.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 0.5709999799728394, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 24.0, 'SpellClassMask_2': 4096, 'SpellClassSet': 11, 'SpellLevel': 75, 'SpellPriority': 50, 'SpellVisualID_1': 11565, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


hex_51514 = spell(
    id=51514,
    name='Hex',
    school=School.NATURE,
    dispel=DispelType.CURSE,
    mechanic=Mechanic.POLYMORPH,
    attributes=1074855936,
    cast_time_ms=1500,
    cooldown_ms=45000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=20.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=AuraType.TRANSFORM, misc_value=13321),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=60),
    ],
    spell_icon_id=3058,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 262144, 'AttributesEx2': 64, 'AttributesEx4': 1610612736, 'AttributesEx5': 32, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Cannot attack or cast spells.', 'AuraInterruptFlags': 524288, 'BaseLevel': 80, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Transforms the enemy into a frog. While hexed, the target cannot attack or cast spells. Damage caused may interrupt the effect. Lasts $d. Only one target can be hexed at a time.  Only works on Humanoids and Beasts.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 664232, 'SpellClassMask_2': 32768, 'SpellClassSet': 11, 'SpellLevel': 80, 'SpellPriority': 50, 'SpellVisualID_1': 12780, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetCreatureType': 65},
)


earthliving_weapon_51730 = spell(
    id=51730,
    name='Earthliving Weapon',
    school=School.NATURE,
    attributes=328192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=0.0,
    effects=[
        Effect(type=54, base_points=1799, misc_value=3345),
    ],
    spell_icon_id=3061,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 30); RealPointsPerLevel from rank1->covers-60 (anchor rank 4 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 8, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Imbue the Shaman's weapon with earthen life. Increases healing done by $51940s2 and each heal has a $<chance>% chance to proc Earthliving on the target, healing an additional $51945o over $51945d. Lasts 30 minutes.", 'EffectBasePoints_2': 19, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 2048, 'SpellClassSet': 11, 'SpellDescriptionVariableID': 101, 'SpellLevel': 30, 'SpellVisualID_1': 8723, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Targets': 16},
)


wind_shear_57994 = spell(
    id=57994,
    name='Wind Shear',
    school=School.NATURE,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=6000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=25.0,
    duration_ms=2000,
    effects=[
        Effect(type=EffectType.INTERRUPT_CAST, base_points=-1, mechanic=26, implicit_target_a=6),
        Effect(type=EffectType.THREAT, base_points=-1, implicit_target_a=6),
    ],
    spell_icon_id=220,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 16, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly blasts the target with a gust of wind, causing no damage but interrupting spellcasting and preventing any spell in that school from being cast for $d. Also lowers your threat, making the enemy less likely to attack you.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 134219776, 'SpellClassSet': 11, 'SpellLevel': 16, 'SpellVisualID_1': 14861},
)


earth_shield_974 = spell(
    id=974,
    name='Earth Shield',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=327680,
    category=1195,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=15,
    range_yards=40.0,
    duration_ms=600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=149, points_per_level=5.5, implicit_target_a=21, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=21, apply_aura=149, misc_value=126),
    ],
    spell_icon_id=2015,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 50); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx4': 524288, 'AttributesEx5': 32, 'AttributesEx6': 67108864, 'AttributesEx7': 1073742848, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Reduces casting or channeling time lost when damaged by $s2% and attacks heal the shielded target for $s1.', 'AuraInterruptFlags': 524288, 'BaseLevel': 50, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Protects the target with an earthen shield, reducing casting or channeling time lost when damaged by $s2%  and causing attacks to heal the shielded target for $<heal>.  This effect can only occur once every few seconds.  $n charges.  Lasts $d.  Earth Shield can only be placed on one target at a time and only one Elemental Shield can be active on a target at a time.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 0.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 6, 'ProcTypeMask': 172712, 'SpellClassMask_2': 1024, 'SpellClassSet': 11, 'SpellDescriptionVariableID': 170, 'SpellLevel': 50, 'SpellVisualID_1': 7362, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


totem_of_wrath_30706 = spell(
    id=30706,
    name='Totem of Wrath',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=44, misc_value=17539),
    ],
    spell_icon_id=2019,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 50); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 50, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Totem of Wrath with $s1 health at the feet of the caster.  The totem increases spell power by $57658s2 for all party and raid members, and increases the critical strike chance of all attacks by $30708s1% against all enemies within $30708a1 yards.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 63, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 4, 'SpellClassMask_1': 536870912, 'SpellClassSet': 11, 'SpellLevel': 50, 'SpellVisualID_1': 221, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


thunderstorm_51490 = spell(
    id=51490,
    name='Thunderstorm',
    school=School.NATURE,
    attributes=65536,
    category=1223,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=45000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=550, points_per_level=44.95, die_sides=79, implicit_target_a=22, implicit_target_b=15, radius_yards=10.0),
        Effect(type=137, base_points=7, implicit_target_a=1),
        Effect(type=EffectType.KNOCK_BACK, base_points=59, implicit_target_a=22, implicit_target_b=15, misc_value=300, radius_yards=10.0),
    ],
    spell_icon_id=3080,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 60); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 4 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx5': 8, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You call down a bolt of lightning, energizing you and damaging nearby enemies within $a1 yards. Restores $s2% mana to you and deals $s1 Nature damage to all nearby enemies, knocking them back 20 yards. This spell is usable while stunned.', 'EffectBonusMultiplier_1': 0.1720000058412552, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 11, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 8192, 'SpellClassSet': 11, 'SpellLevel': 60, 'SpellVisualID_1': 11302, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


riptide_61295 = spell(
    id=61295,
    name='Riptide',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    category=1228,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=6000,
    mana_cost=0,
    mana_cost_pct=18,
    range_yards=40.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.HEAL, base_points=638, points_per_level=48.25, die_sides=53, implicit_target_a=21),
        Effect(type=EffectType.APPLY_AURA, base_points=132, points_per_level=10.05, implicit_target_a=21, apply_aura=AuraType.PERIODIC_HEAL, amplitude=3000),
    ],
    spell_icon_id=3786,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 60); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 4 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx3': 128, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': "Heals $s2 every $t2 seconds.  Increases caster's Chain Heal by $s3%.", 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals a friendly target for $s1 and another $o2 over $d.  Your next Chain Heal cast on that primary target within $d will consume the healing over time effect and increase the amount of the Chain Heal by $s3%.', 'EffectBasePoints_3': 24, 'EffectBonusMultiplier_1': 0.4020000100135803, 'EffectBonusMultiplier_2': 0.18799999356269836, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_3': 16, 'SpellClassSet': 11, 'SpellLevel': 60, 'SpellVisualID_1': 12994, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


elemental_mastery_16166 = spell(
    id=16166,
    name='Elemental Mastery',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=33882112,
    category=1202,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=180000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=108, misc_value=10),
        Effect(type=EffectType.TRIGGER_SPELL, base_points=-1, implicit_target_a=1, trigger_spell=64701),
    ],
    spell_icon_id=117,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx4': 64, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Cast time of your next Lightning Bolt, Chain Lightning or Lava Burst spell is reduced by $s1%.', 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "When activated, your next Lightning Bolt, Chain Lightning or Lava Burst spell becomes an instant cast spell. In addition, you gain $64701s1% spell haste for $64701d. Elemental Mastery shares a cooldown with Nature's Swiftness.", 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 2416967683, 'EffectSpellClassMaskA_2': 12288, 'EffectSpellClassMaskB_1': 3, 'EffectSpellClassMaskB_2': 4096, 'EffectSpellClassMaskC_1': 2416967683, 'EffectSpellClassMaskC_2': 14352, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 69632, 'RangeIndex': 1, 'SpellClassMask_2': 16384, 'SpellClassSet': 11, 'SpellLevel': 1, 'SpellPriority': 50, 'SpellVisualID_1': 290},
)


nature_s_swiftness_16188 = spell(
    id=16188,
    name="Nature's Swiftness",
    school=School.NORMAL,
    dispel=DispelType.MAGIC,
    attributes=33882112,
    category=1202,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=120000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=108, misc_value=10),
    ],
    spell_icon_id=112,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx4': 64, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next Nature spell with a casting time less than 10 secs will be an instant cast spell.', 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "When activated, your next Nature spell with a base casting time less than 10 sec. becomes an instant cast spell. Nature's Swiftness shares a cooldown with Elemental Mastery.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2499, 'EffectSpellClassMaskA_2': 32768, 'EquippedItemClass': -1, 'InterruptFlags': 4, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassMask_2': 128, 'SpellClassSet': 11, 'SpellLevel': 1, 'SpellPriority': 50, 'SpellVisualID_1': 4040},
)


mana_tide_totem_16190 = spell(
    id=16190,
    name='Mana Tide Totem',
    school=School.NORMAL,
    attributes=65536,
    category=591,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=300000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=13000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=42, misc_value=10467),
    ],
    spell_icon_id=94,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 40, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Summons a Mana Tide Totem with $s2% of the caster's health at the feet of the caster for ${$d-1} sec that restores $<mana>% of total mana every $16191t1 seconds to group members within $39610a1 yards.", 'EffectBasePoints_2': 9, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectMiscValueB_1': 82, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 5, 'SpellClassMask_1': 536870912, 'SpellClassSet': 11, 'SpellDescriptionVariableID': 61, 'SpellLevel': 40, 'SpellVisualID_1': 364, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


stormstrike_17364 = spell(
    id=17364,
    name='Stormstrike',
    school=School.NORMAL,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=8000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=5.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=6, apply_aura=271, misc_value=8),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=6, trigger_spell=32175),
        Effect(type=EffectType.TRIGGER_SPELL, base_points=-1, implicit_target_a=6, trigger_spell=32176),
    ],
    spell_icon_id=2562,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 512, 'AttributesEx3': 67108866, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases Nature damage taken from the Shaman by $s1%.', 'BaseLevel': 40, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly attack with both weapons.  In addition, the next $n sources of Nature damage dealt to the target from the Shaman are increased by $17364s1%. Lasts $17364d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1049603, 'EffectSpellClassMaskA_2': 8192, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 100, 'ProcCharges': 4, 'ProcTypeMask': 139808, 'RangeIndex': 2, 'SpellClassMask_2': 16777232, 'SpellClassSet': 11, 'SpellLevel': 40, 'SpellVisualID_1': 7660, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


shamanistic_rage_30823 = spell(
    id=30823,
    name='Shamanistic Rage',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=30824),
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
    ],
    spell_icon_id=2024,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx5': 8, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'All damage taken reduced by $s2% and successful melee attacks have a chance to regenerate mana equal to $s1% of your attack power.', 'BaseLevel': 50, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces all damage taken by $s2% and gives your successful melee attacks a chance to regenerate mana equal to $s1% of your attack power. This spell is usable while stunned. Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassMask_2': 131072, 'SpellClassSet': 11, 'SpellLevel': 50, 'SpellVisualID_1': 47, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


feral_spirit_51533 = spell(
    id=51533,
    name='Feral Spirit',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=12,
    range_yards=30.0,
    duration_ms=45000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=1, implicit_target_a=47, implicit_target_b=1, misc_value=29264, radius_yards=2.0),
    ],
    spell_icon_id=3081,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268436481, 'AttributesEx2': 524288, 'AttributesEx3': 1073872896, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 50, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons two Spirit Wolves under the command of the Shaman, lasting $d.', 'EffectBasePoints_2': -1, 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectDieSides_3': 1, 'EffectMiscValueB_1': 1161, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 65536, 'SpellClassSet': 11, 'SpellLevel': 50, 'SpellVisualID_1': 13077, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


cleanse_spirit_51886 = spell(
    id=51886,
    name='Cleanse Spirit',
    school=School.NATURE,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.DISPEL, implicit_target_a=21, misc_value=4),
        Effect(type=EffectType.DISPEL, implicit_target_a=21, misc_value=3),
        Effect(type=EffectType.DISPEL, implicit_target_a=21, misc_value=2),
    ],
    spell_icon_id=3740,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 40, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Cleanse the spirit of a friendly target, removing 1 poison effect, 1 disease effect, and 1 curse effect.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 8, 'SpellClassSet': 11, 'SpellLevel': 40, 'SpellVisualID_1': 187, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


tidal_force_55198 = spell(
    id=55198,
    name='Tidal Force',
    school=School.NORMAL,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=2000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=59, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=7),
    ],
    spell_icon_id=176,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases the critical effect chance of your Healing Wave, Lesser Healing Wave and Chain Heal by $s1%. Each critical heal reduces the chance by 20%. Lasts $55166d.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical effect chance of your Healing Wave, Lesser Healing Wave and Chain Heal by $55198s1%. Each critical heal reduces the chance by 20%. Lasts $55166d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 448, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_3': 1, 'SpellClassSet': 11, 'SpellLevel': 20, 'SpellVisualID_1': 12092},
)


lava_lash_60103 = spell(
    id=60103,
    name='Lava Lash',
    school=School.FIRE,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=6000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=4,
    range_yards=5.0,
    effects=[
        Effect(type=31, base_points=99, implicit_target_a=6),
        Effect(type=EffectType.DUMMY, base_points=24),
    ],
    spell_icon_id=3741,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 16777216, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 41, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You charge your off-hand weapon with lava, instantly dealing $s1% off-hand Weapon damage. Damage is increased by $s2% if your off-hand weapon is enchanted with Flametongue.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemInvTypes': 4194304, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_3': 4, 'SpellClassSet': 11, 'SpellLevel': 41, 'SpellPriority': 50, 'SpellVisualID_1': 12759, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
