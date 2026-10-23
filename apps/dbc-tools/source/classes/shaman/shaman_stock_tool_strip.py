"""
Shaman - the 75 stock totem ranks nobody else declares (SH0b A7, 0-verify item 2c).

Pulled with pull_dsl.py, otherwise byte-identical to stock: only Totem_1/2 and RequiredTotemCategoryID_1/2 are zeroed so
the cast no longer fails with SPELL_FAILED_TOTEMS (ruling 3A.8) and check_totem_tools stays silent once class set 11 is
tool-free. These ranks are not learnable (no trainer rows); the strip only matters for GM/.learn.
"""

from lib.dsl import Effect
from lib.dsl.registry import spell


# 6365: stock rank, tool columns stripped only (SH0b A7).
searing_totem_6365 = spell(
    id=6365,
    name='Searing Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=0.0,
    duration_ms=45000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=44, misc_value=3904),
    ],
    spell_icon_id=680,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 40, 'SpellLevel': 40, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 63, 'SpellVisualID_1': 221, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Searing Totem with $s1 health at your feet for $d that repeatedly attacks an enemy within $6352r1 yards for $6352s1 Fire damage.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 16, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 10437: stock rank, tool columns stripped only (SH0b A7).
searing_totem_10437 = spell(
    id=10437,
    name='Searing Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=0.0,
    duration_ms=50000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=44, misc_value=7400),
    ],
    spell_icon_id=680,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 50, 'SpellLevel': 50, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 63, 'SpellVisualID_1': 221, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Searing Totem with $s1 health at your feet for $d that repeatedly attacks an enemy within $10435r1 yards for $10435s1 Fire damage.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 16, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 10438: stock rank, tool columns stripped only (SH0b A7).
searing_totem_10438 = spell(
    id=10438,
    name='Searing Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=0.0,
    duration_ms=55000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=44, misc_value=7402),
    ],
    spell_icon_id=680,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 60, 'SpellLevel': 60, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 63, 'SpellVisualID_1': 221, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 6', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Searing Totem with $s1 health at your feet for $d that repeatedly attacks an enemy within $10436r1 yards for $10436s1 Fire damage.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 16, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 25533: stock rank, tool columns stripped only (SH0b A7).
searing_totem_25533 = spell(
    id=25533,
    name='Searing Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=0.0,
    duration_ms=60000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=44, misc_value=15480),
    ],
    spell_icon_id=680,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 69, 'SpellLevel': 69, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 63, 'SpellVisualID_1': 221, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 7', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Searing Totem with $s1 health at your feet for $d that repeatedly attacks an enemy within $25530r1 yards for $25530s1 Fire damage.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 16, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 58699: stock rank, tool columns stripped only (SH0b A7).
searing_totem_58699 = spell(
    id=58699,
    name='Searing Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=0.0,
    duration_ms=60000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=44, misc_value=31162),
    ],
    spell_icon_id=680,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 71, 'SpellLevel': 71, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 63, 'SpellVisualID_1': 221, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 8', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Searing Totem with $s1 health at your feet for $d that repeatedly attacks an enemy within $58700r1 yards for $58700s1 Fire damage.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 16, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 58703: stock rank, tool columns stripped only (SH0b A7).
searing_totem_58703 = spell(
    id=58703,
    name='Searing Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=0.0,
    duration_ms=60000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=44, misc_value=31164),
    ],
    spell_icon_id=680,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 75, 'SpellLevel': 75, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 63, 'SpellVisualID_1': 221, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 9', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Searing Totem with $s1 health at your feet for $d that repeatedly attacks an enemy within $58701r1 yards for $58701s1 Fire damage.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 16, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 58704: stock rank, tool columns stripped only (SH0b A7).
searing_totem_58704 = spell(
    id=58704,
    name='Searing Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=0.0,
    duration_ms=60000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=44, misc_value=31165),
    ],
    spell_icon_id=680,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 80, 'SpellLevel': 80, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 63, 'SpellVisualID_1': 221, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 10', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Searing Totem with $s1 health at your feet for $d that repeatedly attacks an enemy within $58702r1 yards for $58702s1 Fire damage.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 16, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 6375: stock rank, tool columns stripped only (SH0b A7).
healing_stream_totem_6375 = spell(
    id=6375,
    name='Healing Stream Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=42, misc_value=3906),
    ],
    spell_icon_id=1647,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 30, 'SpellLevel': 30, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 82, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Healing Stream Totem with $s1 health at the feet of the caster for $d that heals group members within $52046a1 yards for $6371s1 every $6371t1 seconds.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 524288, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 6377: stock rank, tool columns stripped only (SH0b A7).
healing_stream_totem_6377 = spell(
    id=6377,
    name='Healing Stream Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=42, misc_value=3907),
    ],
    spell_icon_id=1647,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 40, 'SpellLevel': 40, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 82, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Healing Stream Totem with $s1 health at the feet of the caster for $d that heals group members within $52047a1 yards for $6372s1 every $6372t1 seconds.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 524288, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 10462: stock rank, tool columns stripped only (SH0b A7).
healing_stream_totem_10462 = spell(
    id=10462,
    name='Healing Stream Totem',
    school=16,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=42, misc_value=3908),
    ],
    spell_icon_id=1647,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 50, 'SpellLevel': 50, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 82, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Healing Stream Totem with $s1 health at the feet of the caster for $d that heals group members within $52048a1 yards for $10460s1 every $10460t1 seconds.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 524288, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 10463: stock rank, tool columns stripped only (SH0b A7).
healing_stream_totem_10463 = spell(
    id=10463,
    name='Healing Stream Totem',
    school=16,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=42, misc_value=3909),
    ],
    spell_icon_id=1647,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 60, 'SpellLevel': 60, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 82, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Healing Stream Totem with $s1 health at the feet of the caster for $d that heals group members within $52049a1 yards for $10461s1 every $10461t1 seconds.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 524288, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 25567: stock rank, tool columns stripped only (SH0b A7).
healing_stream_totem_25567 = spell(
    id=25567,
    name='Healing Stream Totem',
    school=16,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=42, misc_value=15488),
    ],
    spell_icon_id=1647,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 69, 'SpellLevel': 69, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 82, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 6', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Healing Stream Totem with $s1 health at the feet of the caster for $d that heals group members within $52050a1 yards for $25566s1 every $25566t1 seconds.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 524288, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 58755: stock rank, tool columns stripped only (SH0b A7).
healing_stream_totem_58755 = spell(
    id=58755,
    name='Healing Stream Totem',
    school=16,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=42, misc_value=31181),
    ],
    spell_icon_id=1647,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 71, 'SpellLevel': 71, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 82, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 7', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Healing Stream Totem with $s1 health at the feet of the caster for $d that heals group members within $58759a1 yards for $58763s1 every $58763t1 seconds.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 524288, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 58756: stock rank, tool columns stripped only (SH0b A7).
healing_stream_totem_58756 = spell(
    id=58756,
    name='Healing Stream Totem',
    school=16,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=42, misc_value=31182),
    ],
    spell_icon_id=1647,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 76, 'SpellLevel': 76, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 82, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 8', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Healing Stream Totem with $s1 health at the feet of the caster for $d that heals group members within $58760a1 yards for $58764s1 every $58764t1 seconds.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 524288, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 58757: stock rank, tool columns stripped only (SH0b A7).
healing_stream_totem_58757 = spell(
    id=58757,
    name='Healing Stream Totem',
    school=16,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=42, misc_value=31185),
    ],
    spell_icon_id=1647,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 80, 'SpellLevel': 80, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 82, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 9', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Healing Stream Totem with $s1 health at the feet of the caster for $d that heals group members within $58761a1 yards for $58765s1 every $58765t1 seconds.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 524288, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 6390: stock rank, tool columns stripped only (SH0b A7).
stoneclaw_totem_6390 = spell(
    id=6390,
    name='Stoneclaw Totem',
    school=1,
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
        Effect(type=28, base_points=149, points_per_level=3.0, implicit_target_a=41, misc_value=3911),
    ],
    spell_icon_id=689,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 18, 'SpellLevel': 18, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 81, 'SpellVisualID_1': 362, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Stoneclaw Totem with $s1 health at the feet of the caster for $d that taunts creatures within $6393a1 yards to attack it.  Enemies attacking the Stoneclaw Totem have a $6397h% chance to be stunned for $39796d. Stoneclaw totem also protects all your totems, causing them to absorb $55329s1 damage.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Taunting creatures.', 'AuraDescription_Lang_Mask': 16712190, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 8, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 6391: stock rank, tool columns stripped only (SH0b A7).
stoneclaw_totem_6391 = spell(
    id=6391,
    name='Stoneclaw Totem',
    school=1,
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
        Effect(type=28, base_points=219, points_per_level=3.0, implicit_target_a=41, misc_value=3912),
    ],
    spell_icon_id=689,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 28, 'SpellLevel': 28, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 81, 'SpellVisualID_1': 362, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Stoneclaw Totem with $s1 health at the feet of the caster for $d that taunts creatures within $6394a1 yards to attack it.  Enemies attacking the Stoneclaw Totem have a $6398h% chance to be stunned for $39796d. Stoneclaw totem also protects all your totems, causing them to absorb $55330s1 damage.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Taunting creatures.', 'AuraDescription_Lang_Mask': 16712190, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 8, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 6392: stock rank, tool columns stripped only (SH0b A7).
stoneclaw_totem_6392 = spell(
    id=6392,
    name='Stoneclaw Totem',
    school=1,
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
        Effect(type=28, base_points=279, points_per_level=3.0, implicit_target_a=41, misc_value=3913),
    ],
    spell_icon_id=689,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 38, 'SpellLevel': 38, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 81, 'SpellVisualID_1': 362, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Stoneclaw Totem with $s1 health at the feet of the caster for $d that taunts creatures within $6395a1 yards to attack it.  Enemies attacking the Stoneclaw Totem have a $6399h% chance to be stunned for $39796d. Stoneclaw totem also protects all your totems, causing them to absorb $55332s1 damage.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Taunting creatures.', 'AuraDescription_Lang_Mask': 16712190, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 8, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 10427: stock rank, tool columns stripped only (SH0b A7).
stoneclaw_totem_10427 = spell(
    id=10427,
    name='Stoneclaw Totem',
    school=1,
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
        Effect(type=28, base_points=389, points_per_level=3.0, implicit_target_a=41, misc_value=7398),
    ],
    spell_icon_id=689,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 48, 'SpellLevel': 48, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 81, 'SpellVisualID_1': 362, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Stoneclaw Totem with $s1 health at the feet of the caster for $d that taunts creatures within $10423a1 yards to attack it.  Enemies attacking the Stoneclaw Totem have a $10425h% chance to be stunned for $39796d. Stoneclaw totem also protects all your totems, causing them to absorb $55333s1 damage.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Taunting creatures.', 'AuraDescription_Lang_Mask': 16712190, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 8, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 10428: stock rank, tool columns stripped only (SH0b A7).
stoneclaw_totem_10428 = spell(
    id=10428,
    name='Stoneclaw Totem',
    school=1,
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
        Effect(type=28, base_points=479, points_per_level=3.0, implicit_target_a=41, misc_value=7399),
    ],
    spell_icon_id=689,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 58, 'SpellLevel': 58, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 81, 'SpellVisualID_1': 362, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 6', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Stoneclaw Totem with $s1 health at the feet of the caster for $d that taunts creatures within $10424a1 yards to attack it.  Enemies attacking the Stoneclaw Totem have a $10426h% chance to be stunned for $39796d. Stoneclaw totem also protects all your totems, causing them to absorb $55335s1 damage.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Taunting creatures.', 'AuraDescription_Lang_Mask': 16712190, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 8, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 25525: stock rank, tool columns stripped only (SH0b A7).
stoneclaw_totem_25525 = spell(
    id=25525,
    name='Stoneclaw Totem',
    school=1,
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
        Effect(type=28, base_points=1314, points_per_level=3.0, implicit_target_a=41, misc_value=15478),
    ],
    spell_icon_id=689,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 67, 'SpellLevel': 67, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 81, 'SpellVisualID_1': 362, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 7', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Stoneclaw Totem with $s1 health at the feet of the caster for $d that taunts creatures within $25512a1 yards to attack it.  Enemies attacking the Stoneclaw Totem have a $25513h% chance to be stunned for $39796d. Stoneclaw totem also protects all your totems, causing them to absorb $55278s1 damage.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Taunting creatures.', 'AuraDescription_Lang_Mask': 16712190, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 8, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 58580: stock rank, tool columns stripped only (SH0b A7).
stoneclaw_totem_58580 = spell(
    id=58580,
    name='Stoneclaw Totem',
    school=1,
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
        Effect(type=28, base_points=1399, points_per_level=3.0, implicit_target_a=41, misc_value=31120),
    ],
    spell_icon_id=689,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 71, 'SpellLevel': 71, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 81, 'SpellVisualID_1': 362, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 8', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Stoneclaw Totem with $s1 health at the feet of the caster for $d that taunts creatures within $25512a1 yards to attack it.  Enemies attacking the Stoneclaw Totem have a $25513h% chance to be stunned for $39796d.  Stoneclaw totem also protects all your totems, causing them to absorb $58589s1 damage.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Taunting creatures.', 'AuraDescription_Lang_Mask': 16712190, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 8, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 58581: stock rank, tool columns stripped only (SH0b A7).
stoneclaw_totem_58581 = spell(
    id=58581,
    name='Stoneclaw Totem',
    school=1,
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
        Effect(type=28, base_points=1509, points_per_level=3.0, implicit_target_a=41, misc_value=31121),
    ],
    spell_icon_id=689,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 75, 'SpellLevel': 75, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 81, 'SpellVisualID_1': 362, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 9', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Stoneclaw Totem with $s1 health at the feet of the caster for $d that taunts creatures within $25512a1 yards to attack it.  Enemies attacking the Stoneclaw Totem have a $25513h% chance to be stunned for $39796d. Stoneclaw totem also protects all your totems, causing them to absorb $58590s1 damage.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Taunting creatures.', 'AuraDescription_Lang_Mask': 16712190, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 8, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 58582: stock rank, tool columns stripped only (SH0b A7).
stoneclaw_totem_58582 = spell(
    id=58582,
    name='Stoneclaw Totem',
    school=1,
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
        Effect(type=28, base_points=1619, points_per_level=3.0, implicit_target_a=41, misc_value=31122),
    ],
    spell_icon_id=689,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'MaxLevel': 82, 'BaseLevel': 78, 'SpellLevel': 78, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 81, 'SpellVisualID_1': 362, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 10', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Stoneclaw Totem with $s1 health at the feet of the caster for $d that taunts creatures within $25512a1 yards to attack it.  Enemies attacking the Stoneclaw Totem have a $25513h% chance to be stunned for $39796d. Stoneclaw totem also protects all your totems, causing them to absorb $58591s1 damage.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Taunting creatures.', 'AuraDescription_Lang_Mask': 16712190, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 8, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 8155: stock rank, tool columns stripped only (SH0b A7).
stoneskin_totem_8155 = spell(
    id=8155,
    name='Stoneskin Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=41, misc_value=5920),
    ],
    spell_icon_id=690,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 24, 'SpellLevel': 24, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 81, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Stoneskin Totem with $s1 health at the feet of the caster.  The totem protects party and raid members within $8157a1 yards, increasing armor by $8157s1.  Lasts $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 10406: stock rank, tool columns stripped only (SH0b A7).
stoneskin_totem_10406 = spell(
    id=10406,
    name='Stoneskin Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=41, misc_value=7366),
    ],
    spell_icon_id=690,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 34, 'SpellLevel': 34, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 81, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Stoneskin Totem with $s1 health at the feet of the caster.  The totem protects party and raid members within $10403a1 yards, increasing armor by $10403s1.  Lasts $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 10407: stock rank, tool columns stripped only (SH0b A7).
stoneskin_totem_10407 = spell(
    id=10407,
    name='Stoneskin Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=41, misc_value=7367),
    ],
    spell_icon_id=690,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 44, 'SpellLevel': 44, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 81, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Stoneskin Totem with $s1 health at the feet of the caster.  The totem protects party and raid members within $10404a1 yards, increasing armor by $10404s1.  Lasts $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 10408: stock rank, tool columns stripped only (SH0b A7).
stoneskin_totem_10408 = spell(
    id=10408,
    name='Stoneskin Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=41, misc_value=7368),
    ],
    spell_icon_id=690,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 54, 'SpellLevel': 54, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 81, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 6', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Stoneskin Totem with $s1 health at the feet of the caster.  The totem protects party and raid members within $10405a1 yards, increasing armor by $10405s1.  Lasts $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 25508: stock rank, tool columns stripped only (SH0b A7).
stoneskin_totem_25508 = spell(
    id=25508,
    name='Stoneskin Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=41, misc_value=15470),
    ],
    spell_icon_id=690,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 63, 'SpellLevel': 63, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 81, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 7', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Stoneskin Totem with $s1 health at the feet of the caster.  The totem protects party and raid members within $25506a1 yards, increasing armor by $25506s1.  Lasts $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 25509: stock rank, tool columns stripped only (SH0b A7).
stoneskin_totem_25509 = spell(
    id=25509,
    name='Stoneskin Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=41, misc_value=15474),
    ],
    spell_icon_id=690,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 70, 'SpellLevel': 70, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 81, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 8', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Stoneskin Totem with $s1 health at the feet of the caster.  The totem protects party and raid members within $25507a1 yards, increasing armor by $25507s1.  Lasts $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 58751: stock rank, tool columns stripped only (SH0b A7).
stoneskin_totem_58751 = spell(
    id=58751,
    name='Stoneskin Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=41, misc_value=31175),
    ],
    spell_icon_id=690,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 73, 'SpellLevel': 73, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 81, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 9', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Stoneskin Totem with $s1 health at the feet of the caster.  The totem protects party and raid members within $58752a1 yards, increasing armor by $58752s1.  Lasts $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 58753: stock rank, tool columns stripped only (SH0b A7).
stoneskin_totem_58753 = spell(
    id=58753,
    name='Stoneskin Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=41, misc_value=31176),
    ],
    spell_icon_id=690,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 78, 'SpellLevel': 78, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 81, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 10', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Stoneskin Totem with $s1 health at the feet of the caster.  The totem protects party and raid members within $58754a1 yards, increasing armor by $58754s1.  Lasts $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 8161: stock rank, tool columns stripped only (SH0b A7).
strength_of_earth_totem_8161 = spell(
    id=8161,
    name='Strength of Earth Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=41, misc_value=5922),
    ],
    spell_icon_id=691,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 38, 'SpellLevel': 38, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 81, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Strength of Earth Totem with $s1 health at the feet of the caster.  The totem increases the strength and agility of all party and raid members within $8163a1 yards by $8163s2.  Lasts $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 10442: stock rank, tool columns stripped only (SH0b A7).
strength_of_earth_totem_10442 = spell(
    id=10442,
    name='Strength of Earth Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=41, misc_value=7403),
    ],
    spell_icon_id=691,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 52, 'SpellLevel': 52, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 81, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Strength of Earth Totem with $s1 health at the feet of the caster.  The totem increases the strength and agility of all party and raid members within $10441a1 yards by $10441s2.  Lasts $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 25528: stock rank, tool columns stripped only (SH0b A7).
strength_of_earth_totem_25528 = spell(
    id=25528,
    name='Strength of Earth Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=41, misc_value=15479),
    ],
    spell_icon_id=691,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 65, 'SpellLevel': 65, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 81, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 6', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Strength of Earth Totem with $s1 health at the feet of the caster.  The totem increases the strength and agility of all party and raid members within $25527a1 yards by $25527s2.  Lasts $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 57622: stock rank, tool columns stripped only (SH0b A7).
strength_of_earth_totem_57622 = spell(
    id=57622,
    name='Strength of Earth Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=41, misc_value=30647),
    ],
    spell_icon_id=691,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 75, 'SpellLevel': 75, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 81, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 7', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Strength of Earth Totem with $s1 health at the feet of the caster.  The totem increases the strength and agility of all party and raid members within $57621a1 yards by $57621s2.  Lasts $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 58643: stock rank, tool columns stripped only (SH0b A7).
strength_of_earth_totem_58643 = spell(
    id=58643,
    name='Strength of Earth Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=41, misc_value=31129),
    ],
    spell_icon_id=691,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 80, 'SpellLevel': 80, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 81, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 8', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Strength of Earth Totem with $s1 health at the feet of the caster.  The totem increases the strength and agility of all party and raid members within $58646a1 yards by $58646s2.  Lasts $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 8249: stock rank, tool columns stripped only (SH0b A7).
flametongue_totem_8249 = spell(
    id=8249,
    name='Flametongue Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=11,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=44, misc_value=6012),
    ],
    spell_icon_id=72,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 38, 'SpellLevel': 38, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 63, 'SpellVisualID_1': 221, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Flametongue Totem with $s1 health at the feet of the caster.  Party and raid members within $52110a1 yards of the totem have their spell damage and healing increased by up to $52110s1.  Lasts $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 10526: stock rank, tool columns stripped only (SH0b A7).
flametongue_totem_10526 = spell(
    id=10526,
    name='Flametongue Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=11,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=44, misc_value=7423),
    ],
    spell_icon_id=72,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 48, 'SpellLevel': 48, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 63, 'SpellVisualID_1': 221, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Flametongue Totem with $s1 health at the feet of the caster.  Party and raid members within $52111a1 yards of the totem have their spell damage and healing increased by up to $52111s1.  Lasts $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 16387: stock rank, tool columns stripped only (SH0b A7).
flametongue_totem_16387 = spell(
    id=16387,
    name='Flametongue Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=11,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=44, misc_value=10557),
    ],
    spell_icon_id=72,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 58, 'SpellLevel': 58, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 63, 'SpellVisualID_1': 221, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Flametongue Totem with $s1 health at the feet of the caster.  Party and raid members within $52112a1 yards of the totem have their spell damage and healing increased by up to $52112s1.  Lasts $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 25557: stock rank, tool columns stripped only (SH0b A7).
flametongue_totem_25557 = spell(
    id=25557,
    name='Flametongue Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=11,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=44, misc_value=15485),
    ],
    spell_icon_id=72,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 67, 'SpellLevel': 67, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 63, 'SpellVisualID_1': 221, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Flametongue Totem with $s1 health at the feet of the caster.  Party and raid members within $52113a1 yards of the totem have their spell damage and healing increased by up to $52113s1.  Lasts $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 58649: stock rank, tool columns stripped only (SH0b A7).
flametongue_totem_58649 = spell(
    id=58649,
    name='Flametongue Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=11,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=44, misc_value=31132),
    ],
    spell_icon_id=72,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 71, 'SpellLevel': 71, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 63, 'SpellVisualID_1': 221, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 6', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Flametongue Totem with $s1 health at the feet of the caster.  Party and raid members within $58651a1 yards of the totem have their spell damage and healing increased by up to $58651s1.  Lasts $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 58652: stock rank, tool columns stripped only (SH0b A7).
flametongue_totem_58652 = spell(
    id=58652,
    name='Flametongue Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=11,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=44, misc_value=31158),
    ],
    spell_icon_id=72,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 75, 'SpellLevel': 75, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 63, 'SpellVisualID_1': 221, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 7', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Flametongue Totem with $s1 health at the feet of the caster.  Party and raid members within $58654a1 yards of the totem have their spell damage and healing increased by up to $58654s1.  Lasts $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 58656: stock rank, tool columns stripped only (SH0b A7).
flametongue_totem_58656 = spell(
    id=58656,
    name='Flametongue Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=11,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=44, misc_value=31133),
    ],
    spell_icon_id=72,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 80, 'SpellLevel': 80, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 63, 'SpellVisualID_1': 221, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 8', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Flametongue Totem with $s1 health at the feet of the caster.  Party and raid members within $58655a1 yards of the totem have their spell damage and healing increased by up to $58655s1.  Lasts $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 10478: stock rank, tool columns stripped only (SH0b A7).
frost_resistance_totem_10478 = spell(
    id=10478,
    name='Frost Resistance Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=44, misc_value=7412),
    ],
    spell_icon_id=1713,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 38, 'SpellLevel': 38, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 63, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': "Summons a Frost Resistance Totem with $s1 health at the feet of the caster for $d.  The totem increases party and raid members' frost resistance by $10476s1, if within $10476a1 yards.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 10479: stock rank, tool columns stripped only (SH0b A7).
frost_resistance_totem_10479 = spell(
    id=10479,
    name='Frost Resistance Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=44, misc_value=7413),
    ],
    spell_icon_id=1713,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 54, 'SpellLevel': 54, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 63, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': "Summons a Frost Resistance Totem with $s1 health at the feet of the caster for $d.  The totem increases party and raid members' frost resistance by $10477s1, if within $10477a1 yards.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 25560: stock rank, tool columns stripped only (SH0b A7).
frost_resistance_totem_25560 = spell(
    id=25560,
    name='Frost Resistance Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=44, misc_value=15486),
    ],
    spell_icon_id=1713,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 67, 'SpellLevel': 67, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 63, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': "Summons a Frost Resistance Totem with $s1 health at the feet of the caster for $d.  The totem increases party and raid members' frost resistance by $25559s1, if within $25559a1 yards.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 58741: stock rank, tool columns stripped only (SH0b A7).
frost_resistance_totem_58741 = spell(
    id=58741,
    name='Frost Resistance Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=44, misc_value=31171),
    ],
    spell_icon_id=1713,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 75, 'SpellLevel': 75, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 63, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': "Summons a Frost Resistance Totem with $s1 health at the feet of the caster for $d.  The totem increases party and raid members' frost resistance by $58742s1, if within $58742a1 yards.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 58745: stock rank, tool columns stripped only (SH0b A7).
frost_resistance_totem_58745 = spell(
    id=58745,
    name='Frost Resistance Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=44, misc_value=31172),
    ],
    spell_icon_id=1713,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 80, 'SpellLevel': 80, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 63, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 6', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': "Summons a Frost Resistance Totem with $s1 health at the feet of the caster for $d.  The totem increases party and raid members' frost resistance by $58744s1, if within $58744a1 yards.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 10495: stock rank, tool columns stripped only (SH0b A7).
mana_spring_totem_10495 = spell(
    id=10495,
    name='Mana Spring Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=4,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=42, misc_value=7414),
    ],
    spell_icon_id=338,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 36, 'SpellLevel': 36, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 82, 'SpellVisualID_1': 364, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Mana Spring Totem with $s1 health at the feet of the caster for $d that restores $10491s1 mana every 5 seconds to all party and raid members within $52033a1 yards.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 524288, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 10496: stock rank, tool columns stripped only (SH0b A7).
mana_spring_totem_10496 = spell(
    id=10496,
    name='Mana Spring Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=4,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=42, misc_value=7415),
    ],
    spell_icon_id=338,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 46, 'SpellLevel': 46, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 82, 'SpellVisualID_1': 364, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Mana Spring Totem with $s1 health at the feet of the caster for $d that restores $10493s1 mana every 5 seconds to all party and raid members within $52034a1 yards.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 524288, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 10497: stock rank, tool columns stripped only (SH0b A7).
mana_spring_totem_10497 = spell(
    id=10497,
    name='Mana Spring Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=4,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=42, misc_value=7416),
    ],
    spell_icon_id=338,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 56, 'SpellLevel': 56, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 82, 'SpellVisualID_1': 364, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Mana Spring Totem with $s1 health at the feet of the caster for $d that restores $10494s1 mana every 5 seconds to all party and raid members within $52035a1 yards.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 524288, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 25570: stock rank, tool columns stripped only (SH0b A7).
mana_spring_totem_25570 = spell(
    id=25570,
    name='Mana Spring Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=4,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=42, misc_value=15489),
    ],
    spell_icon_id=338,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 65, 'SpellLevel': 65, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 82, 'SpellVisualID_1': 364, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Mana Spring Totem with $s1 health at the feet of the caster for $d that restores $25569s1 mana every 5 seconds to all party and raid members within $52036a1 yards.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 524288, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 58771: stock rank, tool columns stripped only (SH0b A7).
mana_spring_totem_58771 = spell(
    id=58771,
    name='Mana Spring Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=4,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=42, misc_value=31186),
    ],
    spell_icon_id=338,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 71, 'SpellLevel': 71, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 82, 'SpellVisualID_1': 364, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 6', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Mana Spring Totem with $s1 health at the feet of the caster for $d that restores $58775s1 mana every 5 seconds to all party and raid members within $58778a1 yards.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 524288, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 58773: stock rank, tool columns stripped only (SH0b A7).
mana_spring_totem_58773 = spell(
    id=58773,
    name='Mana Spring Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=4,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=42, misc_value=31189),
    ],
    spell_icon_id=338,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 76, 'SpellLevel': 76, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 82, 'SpellVisualID_1': 364, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 7', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Mana Spring Totem with $s1 health at the feet of the caster for $d that restores $58776s1 mana every 5 seconds to all party and raid members within $58779a1 yards.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 524288, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 58774: stock rank, tool columns stripped only (SH0b A7).
mana_spring_totem_58774 = spell(
    id=58774,
    name='Mana Spring Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=4,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=42, misc_value=31190),
    ],
    spell_icon_id=338,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 80, 'SpellLevel': 80, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 82, 'SpellVisualID_1': 364, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 8', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Mana Spring Totem with $s1 health at the feet of the caster for $d that restores $58777s1 mana every 5 seconds to all party and raid members within $58780a1 yards.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 524288, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 10537: stock rank, tool columns stripped only (SH0b A7).
fire_resistance_totem_10537 = spell(
    id=10537,
    name='Fire Resistance Totem',
    school=16,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=42, misc_value=7424),
    ],
    spell_icon_id=1712,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 42, 'SpellLevel': 42, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 82, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Fire Resistance Totem with $s1 health at the feet of the caster for $d that increases the fire resistance of party and raid members within $10534a1 yards by $10534s1.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 10538: stock rank, tool columns stripped only (SH0b A7).
fire_resistance_totem_10538 = spell(
    id=10538,
    name='Fire Resistance Totem',
    school=16,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=42, misc_value=7425),
    ],
    spell_icon_id=1712,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 58, 'SpellLevel': 58, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 82, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Fire Resistance Totem with $s1 health at the feet of the caster for $d that increases the fire resistance of party and raid members within $10535a1 yards by $10535s1.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 25563: stock rank, tool columns stripped only (SH0b A7).
fire_resistance_totem_25563 = spell(
    id=25563,
    name='Fire Resistance Totem',
    school=16,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=42, misc_value=15487),
    ],
    spell_icon_id=1712,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 68, 'SpellLevel': 68, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 82, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Fire Resistance Totem with $s1 health at the feet of the caster for $d that increases the fire resistance of party and raid members within $25562a1 yards by $25562s1.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 58737: stock rank, tool columns stripped only (SH0b A7).
fire_resistance_totem_58737 = spell(
    id=58737,
    name='Fire Resistance Totem',
    school=16,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=42, misc_value=31169),
    ],
    spell_icon_id=1712,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 75, 'SpellLevel': 75, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 82, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Fire Resistance Totem with $s1 health at the feet of the caster for $d that increases the fire resistance of party and raid members within $58738a1 yards by $58738s1.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 58739: stock rank, tool columns stripped only (SH0b A7).
fire_resistance_totem_58739 = spell(
    id=58739,
    name='Fire Resistance Totem',
    school=16,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=42, misc_value=31170),
    ],
    spell_icon_id=1712,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 80, 'SpellLevel': 80, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 82, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 6', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Fire Resistance Totem with $s1 health at the feet of the caster for $d that increases the fire resistance of party and raid members within $58740a1 yards by $58740s1.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 10585: stock rank, tool columns stripped only (SH0b A7).
magma_totem_10585 = spell(
    id=10585,
    name='Magma Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=27,
    range_yards=0.0,
    duration_ms=21000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=44, misc_value=7464),
    ],
    spell_icon_id=37,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 36, 'SpellLevel': 36, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 63, 'SpellVisualID_1': 369, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Magma Totem with $s1 health at the feet of the caster for ${$d-1} sec that causes $10579s1 Fire damage to creatures within $10579a1 yards every $10582t1 seconds.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 4096, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 10586: stock rank, tool columns stripped only (SH0b A7).
magma_totem_10586 = spell(
    id=10586,
    name='Magma Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=27,
    range_yards=0.0,
    duration_ms=21000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=44, misc_value=7465),
    ],
    spell_icon_id=37,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 46, 'SpellLevel': 46, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 63, 'SpellVisualID_1': 369, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Magma Totem with $s1 health at the feet of the caster for ${$d-1} sec that causes $10580s1 Fire damage to creatures within $10580a1 yards every $10583t1 seconds.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 4096, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 10587: stock rank, tool columns stripped only (SH0b A7).
magma_totem_10587 = spell(
    id=10587,
    name='Magma Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=27,
    range_yards=0.0,
    duration_ms=21000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=44, misc_value=7466),
    ],
    spell_icon_id=37,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 56, 'SpellLevel': 56, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 63, 'SpellVisualID_1': 369, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Magma Totem with $s1 health at the feet of the caster for ${$d-1} sec that causes $10581s1 Fire damage to creatures within $10581a1 yards every $10584t1 seconds.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 4096, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 25552: stock rank, tool columns stripped only (SH0b A7).
magma_totem_25552 = spell(
    id=25552,
    name='Magma Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=27,
    range_yards=0.0,
    duration_ms=21000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=44, misc_value=15484),
    ],
    spell_icon_id=37,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 65, 'SpellLevel': 65, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 63, 'SpellVisualID_1': 369, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Magma Totem with $s1 health at the feet of the caster for ${$d-1} sec that causes $25550s1 Fire damage to creatures within $25550a1 yards every $25551t1 seconds.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 4096, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 58731: stock rank, tool columns stripped only (SH0b A7).
magma_totem_58731 = spell(
    id=58731,
    name='Magma Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=27,
    range_yards=0.0,
    duration_ms=21000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=44, misc_value=31166),
    ],
    spell_icon_id=37,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 73, 'SpellLevel': 73, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 63, 'SpellVisualID_1': 369, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 6', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Magma Totem with $s1 health at the feet of the caster for ${$d-1} sec that causes $58732s1 Fire damage to creatures within $58732a1 yards every $58733t1 seconds.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 4096, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 58734: stock rank, tool columns stripped only (SH0b A7).
magma_totem_58734 = spell(
    id=58734,
    name='Magma Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=27,
    range_yards=0.0,
    duration_ms=21000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=44, misc_value=31167),
    ],
    spell_icon_id=37,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 78, 'SpellLevel': 78, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 63, 'SpellVisualID_1': 369, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 7', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Magma Totem with $s1 health at the feet of the caster for ${$58734d-1} sec that causes $58735s1 Fire damage to creatures within $58735a1 yards every $58736t1 seconds.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 4096, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 10600: stock rank, tool columns stripped only (SH0b A7).
nature_resistance_totem_10600 = spell(
    id=10600,
    name='Nature Resistance Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=43, misc_value=7468),
    ],
    spell_icon_id=1675,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 44, 'SpellLevel': 44, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 83, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Nature Resistance Totem with $s1 health at the feet of the caster for $d that increases the nature resistance of party and raid members within $10598a1 yards by $10598s1.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 10601: stock rank, tool columns stripped only (SH0b A7).
nature_resistance_totem_10601 = spell(
    id=10601,
    name='Nature Resistance Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=43, misc_value=7469),
    ],
    spell_icon_id=1675,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 60, 'SpellLevel': 60, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 83, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Nature Resistance Totem with $s1 health at the feet of the caster for $d that increases the nature resistance of party and raid members within $10599a1 yards by $10599s1.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 25574: stock rank, tool columns stripped only (SH0b A7).
nature_resistance_totem_25574 = spell(
    id=25574,
    name='Nature Resistance Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=43, misc_value=15490),
    ],
    spell_icon_id=1675,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 69, 'SpellLevel': 69, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 83, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Nature Resistance Totem with $s1 health at the feet of the caster for $d that increases the nature resistance of party and raid members within $25573a1 yards by $25573s1.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 58746: stock rank, tool columns stripped only (SH0b A7).
nature_resistance_totem_58746 = spell(
    id=58746,
    name='Nature Resistance Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=43, misc_value=31173),
    ],
    spell_icon_id=1675,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 75, 'SpellLevel': 75, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 83, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Nature Resistance Totem with $s1 health at the feet of the caster for $d that increases the nature resistance of party and raid members within $58748a1 yards by $58748s1.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 58749: stock rank, tool columns stripped only (SH0b A7).
nature_resistance_totem_58749 = spell(
    id=58749,
    name='Nature Resistance Totem',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=43, misc_value=31174),
    ],
    spell_icon_id=1675,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 80, 'SpellLevel': 80, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 83, 'SpellVisualID_1': 319, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 6', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Nature Resistance Totem with $s1 health at the feet of the caster for $d that increases the nature resistance of party and raid members within $58750a1 yards by $58750s1.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 57720: stock rank, tool columns stripped only (SH0b A7).
totem_of_wrath_57720 = spell(
    id=57720,
    name='Totem of Wrath',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=44, misc_value=30652),
    ],
    spell_icon_id=2019,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 60, 'SpellLevel': 60, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 63, 'SpellVisualID_1': 221, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Totem of Wrath with $s1 health at the feet of the caster.  The totem increases spell power by $57660s2 for all party and raid members, and increases the critical strike chance of of all attacks by $30708s1% against all enemies within $30708a1 yards.  Lasts $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 57721: stock rank, tool columns stripped only (SH0b A7).
totem_of_wrath_57721 = spell(
    id=57721,
    name='Totem of Wrath',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=44, misc_value=30653),
    ],
    spell_icon_id=2019,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 70, 'SpellLevel': 70, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 63, 'SpellVisualID_1': 221, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Totem of Wrath with $s1 health at the feet of the caster.  The totem increases the spell power by $57662s2 for all party and raid members, and increases the critical strike chance of all attacks by $30708s1% against all enemies within $30708a1 yards.  Lasts $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)


# 57722: stock rank, tool columns stripped only (SH0b A7).
totem_of_wrath_57722 = spell(
    id=57722,
    name='Totem of Wrath',
    school=1,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=28, base_points=4, implicit_target_a=44, misc_value=30654),
    ],
    spell_icon_id=2019,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 80, 'SpellLevel': 80, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 63, 'SpellVisualID_1': 221, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Totem of Wrath with $s1 health at the feet of the caster.  The totem increases spell power by $57663s2 for all party and raid members, and increases the critical strike chance of all attacks by $30708s1% against all enemies within $30708a1 yards.  Lasts $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000, 'SpellClassSet': 11, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0},
)
