"""
Death Knight - S1a Blood: the pulled stock helper/buff/summon rows the Blood talents edit in place (Blade Barrier buffs, Blood Gorged passives, Scent of Blood buff, Bloody Vengeance buffs,
Bloodworm summon and heals, Vendetta heal). Source of truth: docs/reworks/death-knight-blood-rework.md,
.agents/plans/death-knight-rework/death-knight-rework.S1a-WP-BRIEF.md.
"""

from lib.dsl import AuraType, DispelType, Effect, EffectType, Mechanic, PowerType, School
from lib.dsl.registry import (
    bonus_coefficients, const, custom_attr, linked_spell, scripted_by, skill_line_ability, spell, spell_rune_cost,
    unbind_bonus_coefficients, unbind_script,
)

from . import _masks as m

blade_barrier_64855 = spell(
    id=64855,
    name='Blade Barrier',
    school=1,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=6, base_points=-5, implicit_target_a=1, apply_aura=87, misc_value=127),
        Effect(type=3, base_points=5, implicit_target_a=1),
    ],
    spell_icon_id=85,
    notes='pulled from existing data',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 20, 'SpellLevel': 20, 'RangeIndex': 1, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'SpellVisualID_1': 342, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever your Blood Runes are on cooldown, you gain Blade Barrier, reducing all damage taken by $s1% for $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage taken reduced.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 15, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


blade_barrier_64856 = spell(
    id=64856,
    name='Blade Barrier',
    school=1,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=6, base_points=-7, implicit_target_a=1, apply_aura=87, misc_value=127),
        Effect(type=3, base_points=5, implicit_target_a=1),
    ],
    spell_icon_id=85,
    notes='pulled from existing data',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 20, 'SpellLevel': 20, 'RangeIndex': 1, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'SpellVisualID_1': 342, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever your Blood Runes are on cooldown, you gain Blade Barrier, reducing all damage taken by $s1% for $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage taken reduced.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 15, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


blood_gorged_50108 = spell(
    id=50108,
    name='Blood Gorged',
    school=1,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=6, base_points=5, implicit_target_a=1, apply_aura=79, misc_value=127),
    ],
    spell_icon_id=24,
    notes='pulled from existing data',
    raw_overrides={'CasterAuraState': 23, 'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 20971521, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you are above 75% health, you deal $s1% more damage.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 15, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


blood_gorged_50109 = spell(
    id=50109,
    name='Blood Gorged',
    school=1,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=6, base_points=8, implicit_target_a=1, apply_aura=79, misc_value=127),
    ],
    spell_icon_id=24,
    notes='pulled from existing data',
    raw_overrides={'CasterAuraState': 23, 'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 20971521, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you are above 75% health, you deal $s1% more damage.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 15, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


blood_gorged_61275 = spell(
    id=61275,
    name='Blood Gorged',
    school=1,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=6, base_points=5, implicit_target_a=1, apply_aura=280, misc_value=1),
    ],
    spell_icon_id=24,
    notes='pulled from existing data',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectDieSides_2': 1, 'EffectBasePoints_2': -1, 'ImplicitTargetA_3': 1, 'EffectSpellClassMaskA_1': 20971521, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712188, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 15, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


blood_gorged_61276 = spell(
    id=61276,
    name='Blood Gorged',
    school=1,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=6, base_points=9, implicit_target_a=1, apply_aura=280, misc_value=1),
    ],
    spell_icon_id=24,
    notes='pulled from existing data',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectDieSides_2': 1, 'EffectBasePoints_2': -1, 'ImplicitTargetA_3': 1, 'EffectSpellClassMaskA_1': 20971521, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712188, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 15, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


scent_of_blood_50421 = spell(
    id=50421,
    name='Scent of Blood',
    school=1,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=1,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=20000,
    effects=[
        Effect(type=6, die_sides=0, implicit_target_a=1, apply_aura=42, trigger_spell=1206),
    ],
    spell_icon_id=2283,
    notes='pulled from existing data',
    raw_overrides={'CastingTimeIndex': 1, 'ProcTypeMask': 20, 'ProcChance': 100, 'SpellLevel': 1, 'RangeIndex': 1, 'CumulativeAura': 0, 'ProcCharges': 3, 'EquippedItemClass': -1, 'SpellVisualID_1': 2759, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Your next 3 melee hits generate 10 Runic Power.  This effect lasts $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next melee hits generate Runic Power.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 4, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0},
)


bloody_vengeance_50447 = spell(
    id=50447,
    name='Bloody Vengeance',
    school=1,
    dispel=1,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=30000,
    effects=[
        Effect(type=6, implicit_target_a=1, apply_aura=79, misc_value=127),
    ],
    spell_icon_id=2730,
    notes='pulled from existing data',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'CumulativeAura': 3, 'EquippedItemClass': -1, 'SpellVisualID_1': 6597, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'Increases all damage you deal by $s1% for $d after you deal a critical strike from a weapon swing, spell or ability.  Stacks up to $u times.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage dealt increased.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 10, 'PreventionType': 2, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


bloody_vengeance_50448 = spell(
    id=50448,
    name='Bloody Vengeance',
    school=1,
    dispel=1,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=30000,
    effects=[
        Effect(type=6, base_points=1, implicit_target_a=1, apply_aura=79, misc_value=127),
    ],
    spell_icon_id=2730,
    notes='pulled from existing data',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'CumulativeAura': 3, 'EquippedItemClass': -1, 'SpellVisualID_1': 6597, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'Increases all damage you deal by $s1% for $d after you deal a critical strike from a weapon swing, spell or ability.  Stacks up to $u times.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage dealt increased.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 10, 'PreventionType': 2, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


bloody_vengeance_50449 = spell(
    id=50449,
    name='Bloody Vengeance',
    school=1,
    dispel=1,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=30000,
    effects=[
        Effect(type=6, base_points=2, implicit_target_a=1, apply_aura=79, misc_value=127),
    ],
    spell_icon_id=2730,
    notes='pulled from existing data',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'CumulativeAura': 3, 'EquippedItemClass': -1, 'SpellVisualID_1': 6597, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'Increases all damage you deal by $s1% for $d after you deal a critical strike from a weapon swing, spell or ability.  Stacks up to $u times.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage dealt increased.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 10, 'PreventionType': 2, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


bloodworm_50452 = spell(
    id=50452,
    name='Bloodworm',
    school=32,
    attributes=262144,
    cast_time_ms=0,
    cooldown_ms=300000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=18000,
    effects=[
        Effect(type=28, implicit_target_a=53, misc_value=28017),
    ],
    spell_icon_id=2296,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268435456, 'AttributesEx2': 1, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 66, 'SpellLevel': 66, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 713, 'SpellVisualID_1': 8208, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Creates a Bloodworm to attack nearby targets.  Caster receives health when the Bloodworm deals damage.  Lasts $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'SpellClassSet': 15, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


health_leech_50454 = spell(
    id=50454,
    name='Health Leech',
    school=32,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.HEAL, implicit_target_a=25,
               potency_excluded='amount is the Bloodworm hit damage x BLOODWORM_HEAL_PCT / 100, set by '
                                'spell_dk_bloodworm_heal_rework through BP0, not CalcValue'),
    ],
    spell_icon_id=1942,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 537395200, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 1, 'SpellLevel': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 8226, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': "The Bloodworm's melee attacks siphon blood from the target, converting it into health for its master.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 15, 'SpellClassMask_2': 2097152, 'SpellClassMask_3': m.DK_SELF_HEAL, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


vendetta_50181 = spell(
    id=50181,
    name='Vendetta',
    school=1,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=1,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.HEAL, die_sides=0, implicit_target_a=1,
               potency_excluded='percent of maximum health (the Vendetta rank value), set by spell_dk_vendetta through '
                                'BP0, not CalcValue'),
    ],
    spell_icon_id=3008,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 536870912, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 40, 'SpellLevel': 40, 'RangeIndex': 2, 'EquippedItemClass': -1, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Whenever you kill a target, you are healed for a percentage of your total health.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 15, 'SpellClassMask_2': 1048576, 'SpellClassMask_3': m.DK_SELF_HEAL, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_2': 1.0},
)

# Scent of Blood buff 50421 (D4): three charges (ProcCharges), no cumulative stacking, a re-proc refreshes to 3. The stock
# stack-removing script is replaced by the rework's charge-consuming one (energize 50422 once per cast).
unbind_script(50421, 'spell_dk_scent_of_blood')
scripted_by(50421, 'spell_dk_scent_of_blood_rework')

# Bloodworm summon 50452: the stock script rolls irand(2, 4) worms; the rework script owns the count and the cap.
# 50453 is the stock aura on every Bloodworm 28017 (creature_template_addon): its stock script heals 150%, the rework
# heals BLOODWORM_HEAL_PCT.
unbind_script(50452, 'spell_dk_bloodworms')
scripted_by(50452, 'spell_dk_bloodworms_rework')
unbind_script(50453, 'spell_dk_blood_gorged')
scripted_by(50453, 'spell_dk_bloodworm_heal_rework')


# Bloodworm aura 50453 (stock-only before this pull; every Bloodworm 28017 carries it via creature_template_addon).
health_leech_50453 = spell(
    id=50453,
    name='Health Leech',
    school=1,
    attributes=64,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=6, die_sides=0, implicit_target_a=1, apply_aura=4),
    ],
    spell_icon_id=1942,
    notes='pulled from existing data (S1a m5): doc aura text and tooltip; effects/procs unchanged, script rebind declared above',
    raw_overrides={'AttributesEx2': 524288, 'CastingTimeIndex': 1, 'ProcTypeMask': 4, 'ProcChance': 100, 'BaseLevel': 1, 'SpellLevel': 1, 'DurationIndex': 0, 'EquippedItemClass': -1, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Passive', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': "Attacks its master's target and heals its master for the damage it deals.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Heals its master as it deals damage.', 'AuraDescription_Lang_Mask': 16712190, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)
