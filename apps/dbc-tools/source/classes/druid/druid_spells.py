"""
Druid - player-castable spells (real cast_time_ms/cooldown_ms, not marked passive).

Split from a single source/classes/druid.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .druid_...` below) resolve.
"""

from lib.dsl import AuraType, DispelType, Effect, EffectType, Mechanic, PowerType, School, SpellModOp
from lib.dsl.constants import ShapeshiftForm
from lib.dsl.registry import bonus_coefficients, scripted_by, skill_line_ability, spell, trained_by, unbind_bonus_coefficients
from ._masks import BLOOM, CENARION_WARD, MASS_ENTANGLEMENT, STARSURGE
from ._masks import BERSERK_COST, IRONFUR, PULVERIZE, THRASH, UPHEAVAL  # druid-rework Feral pass
from .druid_trigger_spells import (
    bloom_jump_200561, cenarion_ward_heal_200563, flourish_buff_200565, hurricane_42231,
    starfall_50286, tranquility_44203, typhoon_61391,
)
# druid-rework Feral pass: ShapeshiftMask bits (defined once, in druid_trigger_spells.py).
from .druid_trigger_spells import SS_ANY_BEAR, SS_BEAR, SS_CAT, SS_FERAL, SS_TREE


demoralizing_roar_99 = spell(
    id=99,
    name='Demoralizing Roar',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=100,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-32, points_per_level=-5.428571428571429, implicit_target_a=22, implicit_target_b=15, apply_aura=AuraType.MOD_ATTACK_POWER, radius_yards=10.0),
    ],
    spell_icon_id=960,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 8 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Decreases melee attack power by $s1.', 'BaseLevel': 10, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "The druid roars, decreasing nearby enemies' melee attack power by $s1.  Lasts $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 144, 'SpellClassMask_1': 8, 'SpellClassSet': 7, 'SpellLevel': 10, 'SpellPriority': 50, 'SpellVisualID_1': 3949, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


entangling_roots_339 = spell(
    id=339,
    name='Entangling Roots',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    mechanic=Mechanic.ROOT,
    attributes=1073807360,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=30.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_ROOT),
        Effect(type=EffectType.APPLY_AURA, sp_potency=5.6, potency_kind='periodic', implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
    ],
    spell_icon_id=20,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 8); RealPointsPerLevel from rank1->covers-60 (anchor rank 6 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. Potency system P5 (druid pass): converted to sp_potency=5.6 (potency-report default, base/coef already agreed).',
    raw_overrides={'AttributesEx4': 536872960, 'AttributesEx5': 32, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Rooted.  Causes {pot2} Nature damage every $t2 seconds.', 'AuraInterruptFlags': 4718592, 'BaseLevel': 8, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Roots the target in place and causes {pot2.total} Nature damage over $d.  Damage caused may interrupt the effect.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 664232, 'ShapeshiftExclude': 0, 'SpellClassMask_1': 512, 'SpellClassSet': 7, 'SpellLevel': 8, 'SpellVisualID_1': 38, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


thorns_467 = spell(
    id=467,
    name='Thorns',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=17,
    range_yards=30.0,
    duration_ms=600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, points_per_level=0.9459459459459459, implicit_target_a=21, apply_aura=15),
    ],
    spell_icon_id=53,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 6); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 8 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Causes $s1 Nature damage to attackers.', 'BaseLevel': 6, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Thorns sprout from the friendly target causing $s1 Nature damage to attackers when hit.  Lasts $d.', 'EffectBonusMultiplier_2': 0.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 1073741824, 'SpellClassMask_1': 256, 'SpellClassSet': 7, 'SpellLevel': 6, 'SpellVisualID_1': 201, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


tranquility_740 = spell(
    id=740,
    name='Tranquility',
    school=School.NATURE,
    attributes=65536,
    category=46,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=180000,
    mana_cost=0,
    mana_cost_pct=70,
    range_yards=0.0,
    duration_ms=8000,
    effects=[
        Effect(type=35, base_points=350, points_per_level=53.68, implicit_target_a=29, apply_aura=AuraType.DUMMY, radius_yards=30.0),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=2000, trigger_spell=tranquility_44203.id),
    ],
    spell_icon_id=100,
    notes="pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 30); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 7 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. druid-rework RESTO §7 'Tranquility 740': category_cooldown_ms 480000->180000 (3 min); Cooldown Haste applies to catrec (Player.cpp:11251); scripted_by(740, 'spell_dru_natures_focus_capstone') declared in druid_talents.py.",
    raw_overrides={'AttributesEx': 64, 'AttributesEx2': 1074266112, 'AttributesEx3': 128, 'AttributesEx5': 8192, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Heals nearby party members for $s1 every $t2 seconds.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31756, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals all nearby group members for $s1 every $t2 seconds for $d.  Druid must channel to maintain the spell.', 'EffectBonusMultiplier_1': 0.28600001335144043, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 0, 'ShapeshiftMask': 2, 'SpellClassMask_1': 128, 'SpellClassSet': 7, 'SpellLevel': 30, 'SpellVisualID_1': 1283, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},  # ShapeshiftExclude Moonkin bit dropped - PLAN §11.5 / code review finding #7
)


cat_form_768 = spell(
    id=768,
    name='Cat Form',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=35,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=36, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=17),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=5000),
    ],
    spell_icon_id=493,
    notes='pulled from existing data',
    raw_overrides={'ActiveIconID': 122, 'AttributesEx': 98304, 'AttributesEx4': 2097152, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Immunity to Polymorph effects.  Increases melee attack power by $3025s1 plus Agility.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shapeshift into cat form, increasing melee attack power by $3025s1 plus Agility.  Also protects the caster from Polymorph effects and allows the use of various cat abilities.\r\n\r\nThe act of shapeshifting frees the caster of Polymorph and Movement Impairing effects.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Shapeshift', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 1073741826, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 7, 'SpellLevel': 20, 'SpellVisualID_1': 4228, 'StanceBarOrder': 2, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


# Cat Form (Passive): stock row brought in only to carry one tuning number. Effect 3 is unused by the
# engine (Effect_3 stays 0); its BasePoints is read at runtime by DruidFeralUnitHooks::ModifyMeleeDamage
# (druid_hooks.cpp) as the percentage of normal white-hit damage dealt in Cat Form.
cat_form_passive_3025 = spell(
    id=3025,
    name='Cat Form (Passive)',
    school=8,
    attributes=208,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=6, base_points=39, points_per_level=2.0, implicit_target_a=1, apply_aura=99),
        Effect(type=6, base_points=-30, implicit_target_a=1, apply_aura=10, misc_value=127),
    ],
    spell_icon_id=493,
    notes='DPS balance pass 8 (2026-10-08, user ruling): stock row, only EffectBasePoints_3 changed -1 -> 49 (EffectDieSides_3 stays 1, so CalcValue = 49 + 1 = 50). Effect_3 stays 0 (inert). Slot 3 = percentage of normal white-hit damage in Cat Form; read by DruidFeralUnitHooks::ModifyMeleeDamage via sSpellMgr->GetSpellInfo(3025)->Effects[EFFECT_2].CalcValue().',
    raw_overrides={'AttributesEx': 1024, 'ShapeshiftMask': 1, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 20, 'SpellLevel': 20, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectDieSides_3': 1, 'EffectBasePoints_3': 49, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Passive', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712188, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 7, 'SpellClassMask_1': 134217728, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


faerie_fire_770 = spell(
    id=770,
    name='Faerie Fire',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=30.0,
    duration_ms=300000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-6, implicit_target_a=6, apply_aura=101, misc_value=1),
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=186, misc_value=127),
    ],
    spell_icon_id=109,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 98304, 'AttributesEx2': 524288, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Decreases armor by $s1%.  Cannot stealth or turn invisible.', 'BaseLevel': 18, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Decrease the armor of the target by $s1% for $d.  While affected, the target cannot stealth or turn invisible.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 0, 'ShapeshiftMask': 1073741824, 'SpellClassMask_1': 1024, 'SpellClassSet': 7, 'SpellLevel': 18, 'SpellVisualID_1': 192, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
# druid-rework FERAL §0.10 / PLAN B5: caster Faerie Fire keeps its -5% armor but moves from the Balance
# spellbook tab (SkillLine 574) to Feral Combat (134). Every other column matches the stock SkillLineAbility 6315
# row (Spell 770, ClassMask 1024, MinSkillLineRank 1).
skill_line_ability(id=6315, skill_line=134, spell_id=faerie_fire_770.id, class_mask=1024, min_skill_line_rank=1)


rejuvenation_774 = spell(
    id=774,
    name='Rejuvenation',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=18,
    range_yards=40.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, sp_potency=10.5, potency_kind='heal_periodic', implicit_target_a=21, apply_aura=AuraType.PERIODIC_HEAL, amplitude=3000),
    ],
    spell_icon_id=64,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 4); RealPointsPerLevel from rank1->covers-60 (anchor rank 11 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. Potency system P5 (druid pass): converted to sp_potency=10.5 (potency-report default, base/coef already agreed).',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx3': 128, 'AttributesEx4': 1048576, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Heals {pot1} damage every $t1 seconds.', 'BaseLevel': 4, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals the target for {pot1.total} over $d.', 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 0, 'ShapeshiftMask': 2, 'SpellClassMask_1': 16, 'SpellClassSet': 7, 'SpellDescriptionVariableID': 176, 'SpellLevel': 4, 'SpellVisualID_1': 32, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},  # ShapeshiftExclude Moonkin bit dropped - PLAN §11.5 / code review finding #7
)


swipe_bear_779 = spell(
    id=779,
    name='Swipe (Bear)',
    school=School.NORMAL,
    attributes=262160,
    category=85,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=200,
    mana_cost_pct=0,
    range_yards=8.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=28.8, potency_kind='direct', implicit_target_a=22, implicit_target_b=15, radius_yards=8.0),
    ],
    spell_icon_id=1562,
    notes=(
        "potency-system (PLAN P6 step 5, Feral pass): converted from the single-rank bootstrap "
        "(BasePoints/BaseLevel/SpellLevel kept from rank 1, learn level 16). ap_potency=28.8 is the "
        "druid-potency-report.md base-implied default (ap-only row, old coefficient 0/0.063, "
        "mismatched vs the base-implied 28.8 - base wins per the established P5 convention); "
        "AP coefficient moves 0.063 -> 0.123, base V60 77 -> ~77 (essentially unchanged, by "
        "construction)."
    ),
    raw_overrides={'AttributesEx': 512, 'AttributesEx5': 32768, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 16, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Swipe nearby enemies, inflicting {pot1} damage.  Damage increased by attack power.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'ShapeshiftMask': 144, 'SpellClassMask_2': 1048576, 'SpellClassSet': 7, 'SpellLevel': 16, 'SpellVisualID_1': 189, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


travel_form_783 = spell(
    id=783,
    name='Travel Form',
    school=School.NORMAL,
    attributes=360464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=13,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=36, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=17),
    ],
    spell_icon_id=1476,
    notes='pulled from existing data',
    raw_overrides={'ActiveIconID': 122, 'AttributesEx': 98304, 'AttributesEx4': 2097152, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Immune to Polymorph effects.  Movement speed increased by $5419s1%.', 'BaseLevel': 16, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shapeshift into travel form, increasing movement speed by $5419s1%.  Also protects the caster from Polymorph effects.  Only useable outdoors.\r\n\r\nThe act of shapeshifting frees the caster of Polymorph and Movement Impairing effects.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Shapeshift', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 1073741826, 'SpellClassMask_2': 16384, 'SpellClassSet': 7, 'SpellLevel': 16, 'SpellVisualID_1': 4228, 'StanceBarOrder': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


aquatic_form_1066 = spell(
    id=1066,
    name='Aquatic Form',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=13,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=36, misc_value=4),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=17),
    ],
    spell_icon_id=1475,
    notes='pulled from existing data',
    raw_overrides={'ActiveIconID': 122, 'AttributesEx': 229376, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Immune to Polymorph effects.  Increases swim speed by $5421s1% and allows underwater breathing.', 'AuraInterruptFlags': 256, 'BaseLevel': 16, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shapeshift into aquatic form, increasing swim speed by $5421s1% and allowing the druid to breathe underwater.  Also protects the caster from Polymorph effects.\r\n\r\nThe act of shapeshifting frees the caster of Polymorph and Movement Impairing effects.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Shapeshift', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 1073741826, 'SpellClassMask_1': 536870912, 'SpellClassSet': 7, 'SpellLevel': 16, 'SpellVisualID_1': 775, 'StanceBarOrder': 1, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


rip_1079 = spell(
    id=1079,
    name='Rip',
    school=School.NORMAL,
    mechanic=15,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=30,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, mechanic=15, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=2000, ap_potency=2.28, cp_ap_potency=4.2, potency_kind='periodic'),
    ],
    spell_icon_id=108,
    notes=(
        'potency-system (PLAN P6 step 4, finishers): converted from the single-rank bootstrap '
        '(BasePoints/BaseLevel/SpellLevel kept from rank 1, learn level 20). ap_potency=2.7 is the '
        'flat per-tick part, cp_ap_potency=1.5 is per combo point per tick; together they reproduce '
        'the pre-conversion per-tick total at level 60, 5 combo points, 1000 attack power (95, '
        'summing the stock EffectPointsPerCombo=4 flat per-combo-point line and the '
        'spell_dru_rip::CalculateAmount script\'s 0.01*AP-per-combo-point term) to within 2%. '
        'EffectPointsPerCombo_1 is generated as 0; spell_dru_rip\'s own AP addition is gated behind '
        'SpellPotency::HasRow() (src/server/scripts/Spells/spell_druid.cpp) so it does not double '
        'count on top of the new cp_ap coefficient. cp_ap_potency 1.5 -> 5.0 (2026-10-08, DPS balance pass, user ruling: Rip should be a major damage source and out-damage Rake). Tooltip AP terms rewritten to the live per-tick coefficient (ap_potency/100 + n*cp_ap_potency/100)*(2/3.5). Effect 1 ap_potency 2.7 -> 1.9 (2026-10-08, DPS balance pass, user ruling: Cat -30%). cp_ap_potency 5.0 -> 3.5 (2026-10-08, DPS balance pass, user ruling: Cat -30%). Tooltip AP terms rewritten for 1.9 + n*3.5.'
        ' Effect 1 ap_potency 1.9 -> 2.28, cp_ap_potency 3.5 -> 4.2 (2026-10-08, DPS balance pass, user ruling: Cat Rip x1.20). Tooltip AP terms rewritten for 2.28 + n*4.2.'
    ),
    raw_overrides={'AttributesEx': 1049088, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Bleed damage every $t1 seconds.', 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Finishing move that causes damage over time.  Damage increases per combo point and by your attack power:\r\n   1 point: ${($m1+$b1*1+0.0370*$AP)*$<dur>} damage over $d.\r\n   2 points: ${($m1+$b1*2+0.0610*$AP)*$<dur>} damage over $d.\r\n   3 points: ${($m1+$b1*3+0.0850*$AP)*$<dur>} damage over $d.\r\n   4 points: ${($m1+$b1*4+0.1090*$AP)*$<dur>} damage over $d.\r\n   5 points: ${($m1+$b1*5+0.1330*$AP)*$<dur>} damage over $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 1, 'SpellClassMask_1': 8388608, 'SpellClassMask_3': 2097152, 'SpellClassSet': 7, 'SpellDescriptionVariableID': 165, 'SpellLevel': 20, 'SpellVisualID_1': 3941, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


claw_1082 = spell(
    id=1082,
    name='Claw',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=45,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.WEAPON_DAMAGE, base_points=26, points_per_level=5.716666666666667, implicit_target_a=6),
        Effect(type=EffectType.ADD_COMBO_POINTS, implicit_target_a=6),
    ],
    spell_icon_id=262,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 8 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134218240, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Claw the enemy, causing $s1 additional damage.  Awards $s2 combo $lpoint:points;.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 1, 'SpellClassMask_3': 262144, 'SpellClassSet': 7, 'SpellLevel': 20, 'SpellVisualID_1': 3882, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


mark_of_the_wild_1126 = spell(
    id=1126,
    name='Mark of the Wild',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=24,
    range_yards=30.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, points_per_level=9.177215189873417, implicit_target_a=21, apply_aura=22, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=21, apply_aura=AuraType.MOD_STAT, misc_value=-1),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=21, apply_aura=143, misc_value=126),
    ],
    spell_icon_id=123,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases armor by $s1.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the friendly target's armor by $s1 for $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 262144, 'SpellClassSet': 7, 'SpellLevel': 1, 'SpellPriority': 50, 'SpellVisualID_1': 212, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


rake_1822 = spell(
    id=1822,
    name='Rake',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=40,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=9000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=13.26, potency_kind='direct', mechanic=15, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, ap_potency=13.43, potency_kind='periodic', mechanic=15, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
        Effect(type=EffectType.ADD_COMBO_POINTS, implicit_target_a=6),
    ],
    spell_icon_id=494,
    notes=(
        "potency-system (PLAN P6 step 5, Feral pass): converted from the single-rank bootstrap "
        "(BasePoints/BaseLevel/SpellLevel kept from rank 1, learn level 24). Both effects are "
        "ap-only (old coefficients 0/0.010 direct, 0/0.060 periodic) - ap_potency=44.5 (direct) and "
        "44.9 (periodic) are druid-potency-report.md's base-implied defaults, matching the "
        "established P5 convention for a mismatched ap-only row; AP coefficients move 0.010 -> "
        "0.191 (direct) and 0.060 -> 0.385 (periodic tick), base V60s essentially unchanged by "
        "construction. Effect 1 (direct) ap_potency 44.5 -> 22.3, effect 2 (periodic) ap_potency 44.9 -> 22.5 (2026-10-08, DPS balance pass, user ruling: Rake damage -50%). Effect 1 (direct) ap_potency 22.3 -> 15.6 (2026-10-08, DPS balance pass, user ruling: Cat -30%). Effect 2 (periodic) ap_potency 22.5 -> 15.8 (2026-10-08, DPS balance pass, user ruling: Cat -30%)."
        ' Effect 1 (direct) ap_potency 15.6 -> 13.26, effect 2 (periodic) ap_potency 15.8 -> 13.43 (2026-10-08, DPS balance pass, user ruling: Cat Rake x0.85).'
    ),
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 8, 'AttributesEx4': 1048576, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '{pot2} damage every $t2 seconds.', 'BaseLevel': 24, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Rake the target, causing {pot1} damage and an additional {pot2.total} damage over $d.  Awards $s3 combo $lpoint:points;.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 1, 'SpellClassMask_1': 4096, 'SpellClassSet': 7, 'SpellLevel': 24, 'SpellVisualID_1': 750, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


dash_1850 = spell(
    id=1850,
    name='Dash',
    school=School.NORMAL,
    attributes=262160,
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
        Effect(type=EffectType.APPLY_AURA, base_points=49, points_per_level=0.29411764705882354, implicit_target_a=1, apply_aura=AuraType.MOD_INCREASE_SPEED),
    ],
    spell_icon_id=959,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 26); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 32, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases movement speed by $s1% while in Cat Form.', 'BaseLevel': 26, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases movement speed by $s1% while in Cat Form for $d.  Does not break prowling.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_3': 8, 'SpellClassSet': 7, 'SpellLevel': 26, 'SpellVisualID_1': 2276},
)


hibernate_2637 = spell(
    id=2637,
    name='Hibernate',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    mechanic=Mechanic.SLEEP,
    attributes=1074855936,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=30.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
    ],
    spell_icon_id=44,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 18); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 262144, 'AttributesEx2': 524288, 'AttributesEx5': 32, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Asleep.', 'AuraInterruptFlags': 2, 'BaseLevel': 18, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Forces the enemy target to sleep for up to $d.  Any damage will awaken the target.  Only one target can be forced to hibernate at a time.  Only works on Beasts and Dragonkin.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 0, 'ShapeshiftMask': 1073741824, 'SpellClassMask_1': 16777216, 'SpellClassMask_2': 131072, 'SpellClassMask_3': 32768, 'SpellClassSet': 7, 'SpellLevel': 18, 'SpellPriority': 50, 'SpellVisualID_1': 4999, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetCreatureType': 3},
)


remove_curse_2782 = spell(
    id=2782,
    name='Remove Curse',
    school=School.ARCANE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.DISPEL, implicit_target_a=21, misc_value=2),
    ],
    spell_icon_id=236,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 24, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Dispels $s1 Curse from a friendly target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 4194304, 'SpellClassSet': 7, 'SpellLevel': 24, 'SpellVisualID_1': 186, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


abolish_poison_2893 = spell(
    id=2893,
    name='Abolish Poison',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=67584,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=13,
    range_yards=40.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=21, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=3000, trigger_spell=3137),
        Effect(type=EffectType.DISPEL, implicit_target_a=21, misc_value=4),
    ],
    spell_icon_id=265,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Attempts to cure $3137s1 poison every $t1 seconds.', 'BaseLevel': 26, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Attempts to cure $s2 poison effect on the target, and $3137s1 more poison effect every $t1 seconds for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 4, 'SpellClassSet': 7, 'SpellLevel': 26, 'SpellVisualID_1': 3885, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


soothe_animal_2908 = spell(
    id=2908,
    name='Soothe Animal',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=40.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=6, apply_aura=91),
    ],
    spell_icon_id=454,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 22); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 2228224, 'AttributesEx2': 524288, 'AttributesEx3': 196608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Reduced distance at which target will attack.', 'BaseLevel': 22, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Soothes the target beast, reducing the range at which it will attack you by $s1 yards.  Only affects Beast and Dragonkin targets level 40 or lower.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'MaxTargetLevel': 40, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 0, 'ShapeshiftMask': 1073741824, 'SpellClassMask_1': 16777216, 'SpellClassMask_2': 131072, 'SpellClassMask_3': 8192, 'SpellClassSet': 7, 'SpellLevel': 22, 'SpellPriority': 50, 'SpellVisualID_1': 6439, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetCreatureType': 3},
)


starfire_2912 = spell(
    id=2912,
    name='Starfire',
    school=School.ARCANE,
    attributes=65536,
    cast_time_ms=2500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=12,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=87.6, potency_kind='direct', implicit_target_a=6),
    ],
    spell_icon_id=1485,
    notes="pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->covers-60 (anchor rank 7 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80; druid-rework BALANCE §0.13 (A9): cast 3.5s->2.5s (Starlight Wrath's stock cast-cut is gone, §6 row 0,1), raw CastingTimeIndex dropped (resolves via the plain 2500ms row, 30002); now cleaves (spell_dru_starfire_cleave AfterHit casts 200337, WP-B). Potency system P5 (druid pass): converted to sp_potency=158.6 (potency-report default, base/coef already agreed). mana_cost_pct 16 -> 12 (2026-10-08, DPS balance pass, user ruling: Balance mana). Effect 1 sp_potency 158.6 -> 95.2 (2026-10-08, DPS balance pass, user ruling: Balance damage -40%). Effect 1 sp_potency 95.2 -> 87.6 (2026-10-08, DPS balance pass, user ruling: Balance -8%).",
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes {pot1} Arcane damage to the target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 0, 'ShapeshiftMask': 1073741824, 'SpellClassMask_1': 4, 'SpellClassSet': 7, 'SpellLevel': 20, 'SpellPriority': 50, 'SpellVisualID_1': 1264, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
scripted_by(starfire_2912, 'spell_dru_starfire_cleave')


wrath_5176 = spell(
    id=5176,
    name='Wrath',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=71.6, potency_kind='direct', implicit_target_a=6),
    ],
    spell_icon_id=263,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60 (anchor rank 8 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80; druid-rework BALANCE §0.13 (A9): cast_time_ms now says the 1500ms it already resolved to; raw CastingTimeIndex dropped (resolves via the plain 1500ms row, 30004). Potency system P5 (druid pass): converted to sp_potency=119.3 (potency-report default, base/coef already agreed). mana_cost_pct 11 -> 8 (2026-10-08, DPS balance pass, user ruling: Balance mana). Effect 1 sp_potency 119.3 -> 71.6 (2026-10-08, DPS balance pass, user ruling: Balance damage -40%).',
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes {pot1} Nature damage to the target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 0, 'ShapeshiftMask': 1073741824, 'Speed': 20.0, 'SpellClassMask_1': 1, 'SpellClassSet': 7, 'SpellLevel': 1, 'SpellVisualID_1': 3860, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


healing_touch_5185 = spell(
    id=5185,
    name='Healing Touch',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=2500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=33,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, sp_potency=160.0, potency_kind='heal', implicit_target_a=21),
    ],
    spell_icon_id=962,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 15 @ level 80); coefficient/mana_cost_pct from max rank; MaxLevel set to 80. PLAN A9 (BALANCE §0.13): cast_time_ms=2500, raw CastingTimeIndex (16, 1500ms) dropped so it no longer wins over the typed field. ShapeshiftExclude Moonkin bit dropped - PLAN §11.5 / code review finding #7 (B6 heal-cancel hook needs the heal to be castable in Moonkin at all). Potency system P5 (druid pass): converted to sp_potency=160.0 (potency-report default, base/coef already agreed); description dropped the stock $<min>/$<max> SpellDescriptionVariable range (heal kind has no variance roll, so it is now a single value) for {pot1}.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals a friendly target for {pot1}.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 0, 'SpellClassMask_1': 32, 'SpellClassSet': 7, 'SpellDescriptionVariableID': 28, 'SpellLevel': 1, 'SpellVisualID_1': 58, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


challenging_roar_5209 = spell(
    id=5209,
    name='Challenging Roar',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=150,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=22, implicit_target_b=15, apply_aura=AuraType.MOD_TAUNT, radius_yards=10.0),
    ],
    spell_icon_id=957,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 67108864, 'AttributesEx4': 2048, 'AttributesEx5': 2147483648, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Taunted.', 'BaseLevel': 28, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Forces all nearby enemies within $a1 yards to focus attacks on you for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 144, 'SpellClassMask_3': 1, 'SpellClassSet': 7, 'SpellLevel': 28, 'SpellVisualID_1': 748, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


bash_5211 = spell(
    id=5211,
    name='Bash',
    school=School.NORMAL,
    mechanic=Mechanic.STUN,
    attributes=262160,
    category=32,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=60000,
    power_type=PowerType.RAGE,
    mana_cost=100,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=2000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
    ],
    spell_icon_id=473,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 14); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134480384, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Stunned.', 'BaseLevel': 14, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Stuns the target for $d and interrupts non-player spellcasting for $32747d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 144, 'SpellClassMask_1': 8192, 'SpellClassSet': 7, 'SpellLevel': 14, 'SpellPriority': 50, 'SpellVisualID_1': 3948, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


prowl_5215 = spell(
    id=5215,
    name='Prowl',
    school=School.NORMAL,
    dispel=DispelType.STEALTH,
    attributes=437518352,
    category=38,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, points_per_level=5.0, implicit_target_a=1, apply_aura=16),
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=AuraType.MOD_DECREASE_SPEED),
    ],
    spell_icon_id=103,
    notes='pulled from existing data',
    raw_overrides={'ActiveIconID': 30, 'AttributesEx': 16, 'AttributesEx2': 2097152, 'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Stealthed.  Movement speed slowed by $s2%.', 'AuraInterruptFlags': 15366, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Allows the Druid to prowl around, but reduces your movement speed by $s2%.  Lasts until cancelled.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ExcludeCasterAuraState': 12, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 664232, 'RangeIndex': 1, 'ShapeshiftMask': 1, 'SpellClassMask_1': 16384, 'SpellClassSet': 7, 'SpellLevel': 20, 'SpellVisualID_1': 184, 'StartRecoveryCategory': 1178},
)


tiger_s_fury_5217 = spell(
    id=5217,
    name="Tiger's Fury",
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=40000,
    category_cooldown_ms=40000,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, points_per_level=1.25, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_DONE, misc_value=1),
    ],
    spell_icon_id=1181,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 24); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80; druid-rework FERAL §5: cooldown and category cooldown 30 -> 40 sec',
    raw_overrides={'AttributesEx': 32, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases damage done by $s1.', 'BaseLevel': 24, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases damage done by $s1 for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ExcludeCasterAuraSpell': 50334, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 1, 'SpellClassMask_3': 2048, 'SpellClassSet': 7, 'SpellLevel': 24, 'SpellPriority': 50, 'SpellVisualID_1': 200},
)


shred_5221 = spell(
    id=5221,
    name='Shred',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=40,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=75.8, potency_kind='direct', implicit_target_a=6),
        Effect(type=EffectType.ADD_COMBO_POINTS, implicit_target_a=6),
    ],
    spell_icon_id=147,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 22); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80; Claw 1082 retired, Shred takes its place: energy 60 -> 40, learned at 20 (Claw\'s level; BaseLevel/SpellLevel 22 -> 20, eff0 base 23 -> 14 keeps the level-80 value at ~295), no behind-the-target requirement (tooltip + custom_attr(shred_5221, 0) in druid_talents.py). '
          'potency-system (PLAN P6 step 5 follow-up, 2026-10-01, "the open design question", REVISED): moved off the weapon-damage effect '
          'entirely (user call, 2026-10-01) rather than converting the flat bonus into weapon_potency - Cat/Bear form damage is already a pure '
          'function of level (capped at 60) and attack power (Player::CalculateMinMaxDamage), not real weapon itemization, so modeling it as an '
          'ordinary ap_potency SCHOOL_DAMAGE effect (like Pulverize/Savage Bite/Rake/Ferocious Bite already do) gives exact control with no '
          'reference-DPS assumption and no percent-value cosmetic concerns. ap_potency=108.3 exactly reproduces the prior total at level 60/1000 '
          'AP (753.6, using the already-fixed 224% weapon_potency\'s total - see potency-system.PROGRESS.md\'s "P6 step 5 follow-up" for the '
          'engine-formula derivation of that number) - restoring Shred to its full exact-preserving value (the 450%-rounding compromise is now '
          'moot, since there\'s no percent to round). Dropping SPELL_EFFECT_WEAPON_PERCENT_DAMAGE/WEAPON_DAMAGE removes this spell from '
          'Spell::EffectWeaponDmg entirely, which was the only place "Shred, Maul - Rend and Tear" (SpellFamilyFlags[0] & 0x8800, bonus damage '
          'vs bleeding targets) lived - ported into Spell::EffectSchoolDMG\'s own Druid case (SpellEffects.cpp) so the talent keeps working. Effect 1 ap_potency 108.3 -> 75.8 (2026-10-08, DPS balance pass, user ruling: Cat -30%).',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx2': 1048576, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shred the target, causing {pot1} damage.  Awards $s2 combo $lpoint:points;.  Effects which increase Bleed damage also increase Shred damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 1, 'SpellClassMask_1': 32768, 'SpellClassSet': 7, 'SpellLevel': 20, 'SpellVisualID_1': 3950, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


enrage_5229 = spell(
    id=5229,
    name='Enrage',
    school=School.NORMAL,
    dispel=9,
    mechanic=31,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.PERIODIC_ENERGIZE, amplitude=1000, misc_value=1),
        Effect(type=EffectType.ENERGIZE, base_points=199, implicit_target_a=1, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=94),
    ],
    spell_icon_id=961,
    notes='druid-rework FERAL §5: eff0 periodic rage 1 -> 2 per sec (20 over 10 sec); eff1 20 instant unchanged. The armor penalty came from spell_dru_bear_form_passive (unbound, druid_talents.py), so the tooltip drops it; stock spell_dru_enrage stays bound (King of the Jungle 51185, T10).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Gain $/10;s1 rage per second.', 'BaseLevel': 12, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Generates $/10;s2 rage, and then generates an additional $/10;o1 rage over $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 144, 'SpellClassMask_1': 524288, 'SpellClassSet': 7, 'SpellLevel': 12, 'SpellVisualID_1': 249},
)


bear_form_5487 = spell(
    id=5487,
    name='Bear Form',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=35,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MOD_SHAPESHIFT, misc_value=ShapeshiftForm.DIREBEAR),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=17),
    ],
    spell_icon_id=107,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80; druid-rework FERAL §0.16 / CORE-AUDIT row 37: eff0 form 5 -> 8 - the everyday bear is FORM_DIREBEAR at every level (Bestial Fury 200425 takes FORM_BEAR); tooltips read the form-8 passive 9635 instead of 1178.',
    raw_overrides={'ActiveIconID': 122, 'AttributesEx': 98304, 'AttributesEx4': 2097152, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Immune to Polymorph effects.  Increases melee attack power by $9635s3, armor contribution from cloth and leather items by $9635s1%, and Stamina by $9635s2%.', 'BaseLevel': 10, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shapeshift into bear form, increasing melee attack power by $9635s3, armor contribution from cloth and leather items by $9635s1%, and Stamina by $9635s2%.  Also protects the caster from Polymorph effects and allows the use of various bear abilities.\r\n\r\nThe act of shapeshifting frees the caster of Polymorph and Movement Impairing effects.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 1073741826, 'SpellClassMask_1': 1073741824, 'SpellClassSet': 7, 'SpellLevel': 10, 'SpellVisualID_1': 653, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


mark_of_the_wild_6756 = spell(
    id=6756,
    name='Mark of the Wild',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=24,
    range_yards=30.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=104, implicit_target_a=21, apply_aura=22, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=21, apply_aura=AuraType.MOD_STAT, misc_value=-1),
    ],
    spell_icon_id=123,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by quest_template reward/display spell)',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases armor by $s1 and all attributes by $s2.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the friendly target's armor by $s1 and all attributes by $s2 for $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 262144, 'SpellClassSet': 7, 'SpellLevel': 20, 'SpellPriority': 50, 'SpellVisualID_1': 212, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


ravage_6785 = spell(
    id=6785,
    name='Ravage',
    school=School.NORMAL,
    attributes=2359312,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=40,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=232.0, potency_kind='direct', implicit_target_a=6),
        Effect(type=EffectType.ADD_COMBO_POINTS, implicit_target_a=6),
    ],
    spell_icon_id=1531,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 32); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 7 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80; druid-rework FERAL §7 notes: attributes drop SPELL_ATTR0_ONLY_STEALTHED (0x20000) - the client checks it itself; spell_dru_ravage requires stealth unless Stampede (Cat) 200434 is up; energy 60 -> 40. '
          'potency-system (P6 step 5 follow-up, 2026-10-01): moved off the weapon-damage effects entirely (same reasoning as Maul/Shred - Cat '
          'Form damage is already a pure function of level and attack power, not real itemization). This was found not yet mentioned in any '
          'prior pass: eff1 was a flat WEAPON_DAMAGE bonus (41 + 8.71/level), eff2 was a hand-set WEAPON_PERCENT_DAMAGE at base_points=384 - '
          'with the default die_sides=1, that was actually dealing 385% live, the same pre-existing off-by-one Mangle/Swipe/Shred had, never '
          'caught before now. Replaced both with one SCHOOL_DAMAGE effect, ap_potency=232.0, exactly reproducing the old total (1614.8 at '
          'level 60/1000 AP). Checked SpellFamilyFlags (SpellClassMask_1=65536, no SpellClassMask_2) against Spell::EffectWeaponDmg\'s two '
          'Druid-specific special cases (Mangle (Cat): CP at flags[1]&0x400, Shred/Maul\'s Rend and Tear at flags[0]&0x8800) - neither matches, '
          'so no behavior needed porting, unlike Shred/Maul.',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx2': 1048576, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 32, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Ravage the target, causing {pot1} damage.  Must be prowling and behind the target.  Awards $s2 combo $lpoint:points;.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 1, 'SpellClassMask_1': 65536, 'SpellClassSet': 7, 'SpellLevel': 32, 'SpellPriority': 50, 'SpellVisualID_1': 2275, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


maul_6807 = spell(
    id=6807,
    name='Maul',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=5000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=250,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=74.28, potency_kind='direct', implicit_target_a=6),
    ],
    spell_icon_id=261,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 10 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80; druid-rework FERAL §5: no longer on-next-swing (attributes 1044 -> 262160: drops ON_NEXT_SWING/ON_NEXT_SWING_NO_DAMAGE, adds DO_NOT_SHEATH), bear GCD, 5 sec cooldown (below 30 sec, so no Cooldown Haste), 25 rage; spell_dru_maul grants Swell in Bestial Fury. '
          'potency-system (P6 step 5 follow-up, 2026-10-01, "the open design question", REVISED): moved off the weapon-damage effect entirely '
          '(user call, 2026-10-01) rather than converting the flat bonus into weapon_potency - Cat/Bear form damage is already a pure function '
          'of level (capped at 60) and attack power (Player::CalculateMinMaxDamage), not real weapon itemization, so modeling it as an ordinary '
          'ap_potency SCHOOL_DAMAGE effect (like Pulverize/Savage Bite/Rake/Ferocious Bite already do) gives exact control with no reference-DPS '
          'assumption needed. ap_potency=123.8 exactly reproduces the prior total at level 60/1000 AP/2H weapon (861.6 - see '
          'potency-system.PROGRESS.md\'s "P6 step 5 follow-up" for the engine-formula derivation of that number, which no longer matters for '
          'Maul\'s own live behavior now that it isn\'t a weapon effect, only as the preservation target). Dropping '
          'SPELL_EFFECT_NORMALIZED_WEAPON_DMG/WEAPON_PERCENT_DAMAGE removes this spell from Spell::EffectWeaponDmg entirely, which was the only '
          'place "Shred, Maul - Rend and Tear" (SpellFamilyFlags[0] & 0x8800, bonus damage vs bleeding targets) lived - ported into '
          'Spell::EffectSchoolDMG\'s own Druid case (SpellEffects.cpp) so the talent keeps working.'
          ' Effect 1 ap_potency 123.8 -> 99.04 (2026-10-08, DPS balance pass, user ruling: Bear DPS Maul x0.80).'
          ' Effect 1 ap_potency 99.04 -> 74.28 (2026-10-08, DPS balance pass, user ruling: Bear DPS Maul x0.75, round 9).',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx2': 4096, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 10, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A strong attack that deals {pot1} damage and causes a high amount of threat.  While Bestial Fury is active, Maul grants 1 stack of Swell and has a 15% chance to grant Tooth and Claw.  Effects which increase Bleed damage also increase Maul damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 144, 'SpellClassMask_1': 2048, 'SpellClassSet': 7, 'SpellLevel': 10, 'SpellVisualID_1': 166, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
scripted_by(maul_6807, 'spell_dru_maul')  # druid-rework FERAL §5: AfterCast AddSwell(1) in Bestial Fury


moonfire_8921 = spell(
    id=8921,
    name='Moonfire',
    school=School.ARCANE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=15,
    range_yards=30.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, sp_potency=13.8, potency_kind='periodic', implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=56.1, potency_kind='direct', implicit_target_a=6),
    ],
    spell_icon_id=225,
    notes="pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 4); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 14 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80; druid-rework BALANCE §0.13: duration 9s->12s (WotLK max rank; the single-rank bootstrap kept rank 1's 9s DurationIndex), 4 ticks at 3s; druid-rework FERAL §5 / §0.9: ShapeshiftExclude gains cat, bear and dire bear (0x91) so the client also refuses/auto-unshifts. Potency system P5 (druid pass): converted to sp_potency=27.7 (eff1, periodic) / 112.9 (eff2, direct) (potency-report default, base/coef already agreed). mana_cost_pct 21 -> 15 (2026-10-08, DPS balance pass, user ruling: Balance mana). Effect 1 (periodic) sp_potency 27.7 -> 16.6, effect 2 (direct) sp_potency 112.9 -> 67.7 (2026-10-08, DPS balance pass, user ruling: Balance damage -40%). Effect 1 sp_potency 16.6 -> 15.3 (2026-10-08, DPS balance pass, user ruling: Balance -8%). Effect 2 sp_potency 67.7 -> 62.3 (2026-10-08, DPS balance pass, user ruling: Balance -8%). Effect 1 (periodic) sp_potency 15.3 -> 13.8 (2026-10-08, DPS balance pass, user ruling: Balance -10%). Effect 2 (direct) sp_potency 62.3 -> 56.1 (2026-10-08, DPS balance pass, user ruling: Balance -10%).",
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '{pot1} Arcane damage every $t1 seconds.', 'BaseLevel': 4, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Burns the enemy for {pot2} Arcane damage and then an additional {pot1.total} Arcane damage over $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': SS_FERAL, 'ShapeshiftMask': 1073741824, 'SpellClassMask_1': 2, 'SpellClassSet': 7, 'SpellDescriptionVariableID': 176, 'SpellLevel': 4, 'SpellVisualID_1': 1263, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


regrowth_8936 = spell(
    id=8936,
    name='Regrowth',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=29,
    range_yards=40.0,
    duration_ms=21000,
    effects=[
        Effect(type=EffectType.HEAL, sp_potency=153.3, potency_kind='heal', implicit_target_a=21),
        Effect(type=EffectType.APPLY_AURA, sp_potency=11.3, potency_kind='heal_periodic', implicit_target_a=21, apply_aura=AuraType.PERIODIC_HEAL, amplitude=3000),
    ],
    spell_icon_id=197,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 12); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 12 @ level 80); coefficient/mana_cost_pct from max rank; MaxLevel set to 80. PLAN A9 (BALANCE §0.13): cast_time_ms=1500, raw CastingTimeIndex (5, 2000ms) dropped. ShapeshiftExclude Moonkin bit dropped - PLAN §11.5 / code review finding #7. druid-rework FERAL §5 / §0.9: ShapeshiftMask gains cat, bear and dire bear (0x91) next to tree; moonkin stays castable via ALLOW_WHILE_NOT_SHAPESHIFTED (AttributesEx2 0x80000). Potency system P5 (druid pass): converted to sp_potency=153.3 (eff1, heal) / 11.3 (eff2, heal_periodic) (potency-report default, base/coef already agreed).',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx3': 128, 'AttributesEx4': 1048576, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Heals {pot2} every $t2 seconds.', 'BaseLevel': 12, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals a friendly target for {pot1} and another {pot2.total} over $d.', 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 0, 'ShapeshiftMask': SS_TREE | SS_FERAL, 'SpellClassMask_1': 64, 'SpellClassSet': 7, 'SpellDescriptionVariableID': 176, 'SpellLevel': 12, 'SpellVisualID_1': 58, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


cower_8998 = spell(
    id=8998,
    name='Cower',
    school=School.NORMAL,
    attributes=262160,
    category=84,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    power_type=PowerType.ENERGY,
    mana_cost=20,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.THREAT, base_points=-241, points_per_level=-62.26923076923077, implicit_target_a=6),
    ],
    spell_icon_id=958,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 28); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 134217728, 'AttributesEx2': 67108864, 'AttributesEx3': 65536, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 28, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Cower, causing no damage but lowering your threat a small amount, making the enemy less likely to attack you.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 1, 'SpellClassMask_2': 536870912, 'SpellClassSet': 7, 'SpellLevel': 28, 'SpellVisualID_1': 3883, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


pounce_9005 = spell(
    id=9005,
    name='Pounce',
    school=School.NORMAL,
    attributes=2490384,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=50,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=3000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, mechanic=Mechanic.STUN, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=6, trigger_spell=9007),
        Effect(type=EffectType.ADD_COMBO_POINTS, implicit_target_a=6),
    ],
    spell_icon_id=495,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 36); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'ActiveIconID': 495, 'AttributesEx': 134218240, 'AttributesEx2': 1048576, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Stunned.', 'BaseLevel': 36, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Pounce, stunning the target for $d and causing $9007o1 damage over $9007d.  Must be prowling.  Awards $s3 combo $lpoint:points;.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 1, 'SpellClassMask_1': 131072, 'SpellClassSet': 7, 'SpellLevel': 36, 'SpellPriority': 50, 'SpellVisualID_1': 3942, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


mark_of_the_wild_9884 = spell(
    id=9884,
    name='Mark of the Wild',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=24,
    range_yards=30.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=239, implicit_target_a=21, apply_aura=22, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=21, apply_aura=AuraType.MOD_STAT, misc_value=-1),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=21, apply_aura=143, misc_value=126),
    ],
    spell_icon_id=123,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by quest_template reward/display spell)',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases armor by $s1, all attributes by $s2 and all resistances by $s3.', 'BaseLevel': 50, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the friendly target's armor by $s1, all attributes by $s2 and all resistances by $s3 for $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 6', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 262144, 'SpellClassSet': 7, 'SpellLevel': 50, 'SpellPriority': 50, 'SpellVisualID_1': 212, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


nature_s_grasp_16689 = spell(
    id=16689,
    name="Nature's Grasp",
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    category=531,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=60000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=45000,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=19975),
    ],
    spell_icon_id=168,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1->covers-60 (anchor rank 6 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Melee damage you take has a chance to entangle the enemy.', 'BaseLevel': 10, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While active, any time an enemy strikes the caster they have a $h% chance to become afflicted by Entangling Roots (Rank 1). $n charges.  Lasts $d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 3, 'ProcTypeMask': 40, 'RangeIndex': 1, 'ShapeshiftMask': 1073741969, 'SpellClassMask_1': 1048576, 'SpellClassMask_3': 4096, 'SpellClassSet': 7, 'SpellLevel': 10, 'SpellVisualID_1': 212, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


faerie_fire_feral_16857 = spell(
    id=16857,
    name='Faerie Fire (Feral)',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=16,
    category=1133,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=6000,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=300000,
    effects=[
        None,
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=186, misc_value=127),
    ],
    spell_icon_id=109,
    notes='druid-rework FERAL §5 / PLAN B5: eff0 (-5% armor, MOD_RESISTANCE_PCT) removed - the armor reduction moved to Thrash 200423; eff2 (stealth/invisibility reveal) and the bear damage/threat precast 60089 (Spell.cpp) kept.',
    raw_overrides={'AttributesEx': 98304, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Cannot stealth or turn invisible.', 'BaseLevel': 18, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While affected, the target cannot stealth or turn invisible for $d.  Deals ${$AP*0.15+1} damage and additional threat when used in Bear Form or Dire Bear Form.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 145, 'SpellClassMask_1': 1024, 'SpellClassSet': 7, 'SpellLevel': 18, 'SpellVisualID_1': 192, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


hurricane_16914 = spell(
    id=16914,
    name='Hurricane',
    school=School.NATURE,
    attributes=65536,
    category=571,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=81,
    range_yards=30.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.PERSISTENT_AREA_AURA, base_points=-1, mechanic=Mechanic.SNARE, implicit_target_a=28, apply_aura=AuraType.MOD_DECREASE_SPEED, radius_yards=8.0),
        Effect(type=EffectType.PERSISTENT_AREA_AURA, base_points=-21, mechanic=8, implicit_target_a=28, apply_aura=138, radius_yards=8.0),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=1000, trigger_spell=hurricane_42231.id),
    ],
    spell_icon_id=220,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 40); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 140, 'AttributesEx2': 4718592, 'AttributesEx5': 134225920, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$42231s1 damage every $t3 seconds, and time between attacks increased by $s2%.', 'BaseLevel': 40, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31756, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Creates a violent storm in the target area causing $42231s1 Nature damage to enemies every $16914t3 sec,$?s54831[ reducing movement speed by $54831s1%, ][ ]and increasing the time between attacks of enemies by $16914s2%.  Lasts $16914d.  Druid must channel to maintain the spell.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 0, 'ShapeshiftMask': 1073741824, 'SpellClassMask_1': 4194304, 'SpellClassSet': 7, 'SpellLevel': 40, 'SpellVisualID_1': 9489, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Targets': 64},
)


entangling_roots_19975 = spell(
    id=19975,
    name='Entangling Roots',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    mechanic=Mechanic.ROOT,
    attributes=1224802304,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_ROOT),
        Effect(type=EffectType.APPLY_AURA, sp_potency=5.6, potency_kind='periodic', implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
    ],
    spell_icon_id=20,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 8); RealPointsPerLevel from rank1->covers-60 (anchor rank 6 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. Potency system P5 (druid pass): converted to sp_potency=5.6 (potency-report default, base/coef already agreed).',
    raw_overrides={'AttributesEx4': 536872960, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Rooted.  Causes {pot2} Nature damage every $t2 seconds.', 'AuraInterruptFlags': 4718592, 'BaseLevel': 8, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Roots the target in place and causes {pot2.total} Nature damage over $d.  Damage caused may interrupt the effect.  Only useable outdoors.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 664232, 'SpellClassMask_1': 512, 'SpellClassSet': 7, 'SpellLevel': 8, 'SpellVisualID_1': 38, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


rebirth_20484 = spell(
    id=20484,
    name='Rebirth',
    school=School.NATURE,
    attributes=65536,
    category=26,
    cast_time_ms=2000,
    cooldown_ms=0,
    category_cooldown_ms=600000,
    mana_cost=0,
    mana_cost_pct=68,
    range_yards=30.0,
    effects=[
        Effect(type=113, base_points=399, points_per_level=100.0, misc_value=700),
    ],
    spell_icon_id=24,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 7 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx3': 16, 'AttributesEx4': 65536, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 5, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Returns the spirit to the body, restoring a dead target to life with $s1 health and $q mana.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ReagentCount_1': 1, 'Reagent_1': 17034, 'ShapeshiftExclude': 1073741824, 'SpellClassMask_1': 285212672, 'SpellClassSet': 7, 'SpellLevel': 20, 'SpellPriority': 50, 'SpellVisualID_1': 344, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Targets': 32768},
)


gift_of_the_wild_21849 = spell(
    id=21849,
    name='Gift of the Wild',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=64,
    range_yards=40.0,
    duration_ms=3600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=239, points_per_level=17.0, implicit_target_a=56, apply_aura=22, misc_value=1, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=9, points_per_level=0.9, implicit_target_a=56, apply_aura=AuraType.MOD_STAT, misc_value=-1, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=14, points_per_level=1.3, implicit_target_a=56, apply_aura=143, misc_value=126, radius_yards=100.0),
    ],
    spell_icon_id=2435,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 50); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 4 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases armor by $s1, all attributes by $s2 and all resistances by $s3.', 'BaseLevel': 50, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives the Gift of the Wild to all party and raid members, increasing armor by $s1, all attributes by $s2 and all resistances by $s3 for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17021, 'SpellClassMask_1': 262144, 'SpellClassSet': 7, 'SpellLevel': 50, 'SpellPriority': 50, 'SpellVisualID_1': 212, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
# Only on a stock TrainerId no NPC uses; 216 is the live Druid trainer (docs/spell_learn_level.md).
trained_by(gift_of_the_wild_21849, trainer_id=216, req_level=50, money_cost=23000)


gift_of_the_wild_21850 = spell(
    id=21850,
    name='Gift of the Wild',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=64,
    range_yards=40.0,
    duration_ms=3600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=284, implicit_target_a=56, apply_aura=22, misc_value=1, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=56, apply_aura=AuraType.MOD_STAT, misc_value=-1, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=56, apply_aura=143, misc_value=126, radius_yards=100.0),
    ],
    spell_icon_id=2435,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid)',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases armor by $s1, all attributes by $s2 and all resistances by $s3.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives the Gift of the Wild to all party and raid members, increasing armor by $s1, all attributes by $s2 and all resistances by $s3 for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17026, 'SpellClassMask_1': 262144, 'SpellClassSet': 7, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 212, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


ferocious_bite_22568 = spell(
    id=22568,
    name='Ferocious Bite',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=35,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(
            type=EffectType.SCHOOL_DAMAGE, base_potency=60.45, cp_ap_potency=31.85, cp_base_potency=26.24,
            potency_kind='direct', implicit_target_a=6,
        ),
    ],
    spell_icon_id=1680,
    notes=(
        'potency-system (PLAN P6 step 5, Feral pass): converted from the single-rank bootstrap '
        '(BasePoints/BaseLevel/SpellLevel kept from rank 1, learn level 32). base_potency=31.0 '
        'reproduces the pre-conversion CalcValue-only average at level 60 (83, die_sides=17 '
        'included - potency-report default, V60/C60); it carries no sp_potency/ap_potency since '
        "the flat hit never scaled with either stat even in stock. cp_ap_potency=16.333 alone would "
        'give the right AP coefficient (0.07, matching the old hard-coded ap*combo*0.07 term) but '
        'the wrong cp_line (43.7 instead of 36, since a bare cp_ap_potency ties the two at a fixed '
        "ratio - docs/potency-system.md's worked derivation) - cp_base_potency=13.458 (new field, "
        'PLAN P6 step 5, mirroring base_potency for the per-combo line) independently pins cp_line '
        'back to 36, matching the old EffectPointsPerCombo_1=36. Together these reproduce the old '
        'per-combo contribution (36 + 0.07*AP) exactly. EffectPointsPerCombo_1 is generated as 0; '
        "the SpellEffects.cpp hard-coded ap*combo*0.07 term is gated behind SpellPotency::HasRow() "
        '(already done in P6 step 3/4, confirmed still correct here). The energy-conversion AP bonus '
        '(ap/410 per bonus energy point, 0-29 player-variable) is DROPPED entirely rather than '
        'replaced - no single "current total" to preserve since the bonus energy spent varies by '
        'player/rotation; this is a real, intentional reduction in Ferocious Bite\'s average damage '
        '(up to ~7% of attack power in the rare case of a full 29-energy dump) in exchange for a '
        'clean coefficient - see the C++ comment at its gate for the parallel writeup. DieSides 17 '
        "(a much wider roll than every other potency effect's standard +-5%) is replaced by the "
        'system-standard +-5% roll, same system-wide tradeoff already accepted for every other '
        'converted direct effect (not Feral-specific). Tooltip: dropped "+$AP/410" from the energy-'
        'conversion sentence (actively wrong now that the term is gone); the per-combo-point bullet '
        'list is left referencing $b1/0.07*$AP as stale text, same as Eviscerate/Rip in P6 step 4 - '
        'not re-derived into {pot1}-style placeholders (tooltip placeholder migration for finishers '
        'is still an open item, see docs/potency-system.md\'s action items).'
        ' Effect 1 base_potency 31.0 -> 46.5, cp_ap_potency 16.333 -> 24.5, cp_base_potency 13.458 -> 20.187 (2026-10-08, DPS balance pass, user ruling: Cat Ferocious Bite x1.50). No C++ script computes its damage (SpellEffects.cpp only gates the legacy term).'
        ' Effect 1 base_potency 46.5 -> 60.45, cp_ap_potency 24.5 -> 31.85, cp_base_potency 20.187 -> 26.24 (2026-10-08, DPS balance pass, user ruling: Cat Ferocious Bite x1.30, round 9).'
    ),
    raw_overrides={'AttributesEx': 1049088, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 32, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Finishing move that causes damage per combo point and converts each extra point of energy (up to a maximum of $s2 extra energy) into $f1.1 additional damage.  Damage is increased by your attack power.\r\n   1 point  : ${$m1+$b1*1+0.07*$AP}-${$M1+$b1*1+0.07*$AP} damage\r\n   2 points: ${$m1+$b1*2+0.14*$AP}-${$M1+$b1*2+0.14*$AP} damage\r\n   3 points: ${$m1+$b1*3+0.21*$AP}-${$M1+$b1*3+0.21*$AP} damage\r\n   4 points: ${$m1+$b1*4+0.28*$AP}-${$M1+$b1*4+0.28*$AP} damage\r\n   5 points: ${$m1+$b1*5+0.35*$AP}-${$M1+$b1*5+0.35*$AP} damage', 'EffectBasePoints_2': 29, 'EffectBonusMultiplier_1': 0.0, 'EffectChainAmplitude_1': 0.699999988079071, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'RangeIndex': 2, 'ShapeshiftMask': 1, 'SpellClassMask_1': 8388608, 'SpellClassSet': 7, 'SpellLevel': 32, 'SpellVisualID_1': 6587, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


maim_22570 = spell(
    id=22570,
    name='Maim',
    school=School.NORMAL,
    attributes=262160,
    category=33,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    power_type=PowerType.ENERGY,
    mana_cost=35,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=25.5, cp_base_potency=31.402, potency_kind='direct', implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, mechanic=Mechanic.STUN, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
    ],
    spell_icon_id=1681,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 62); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 2 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. '
          'potency-system (P6 step 5 follow-up, 2026-10-01): a previously-unconverted finisher, found during the Maul/Shred/Ravage/Mangle audit '
          '- not in any prior pass\'s report. eff1 was WEAPON_DAMAGE (44 + 1.1667/level) with EffectPointsPerCombo_1=84 (a genuine combo-point '
          'finisher, same category as Eviscerate/Rip/Ferocious Bite), SpellLevel=62 - the first potency-converted ability whose SpellLevel sits '
          'above the system\'s usual 60 reference (its own rank 1 really was learned at 62; a level-60 character cannot cast this at all, so the '
          'preservation target below is evaluated at level 62, not 60). Moved off WEAPON_DAMAGE to SCHOOL_DAMAGE (same reasoning as Maul/Shred/ '
          'Ravage/Mangle); ap_potency=25.5 (flat, no combo) reproduces the old flat hit + Cat Form\'s own raw weapon roll at level 62 (179.4); '
          'cp_base_potency=31.402 (no cp_ap_potency - the old EffectPointsPerCombo=84 carried no attack-power term at all) reproduces the old '
          'per-combo-point line exactly (cp_line=84.0, cp_ap=0.0). Checked SpellFamilyFlags (SpellClassMask_2=128) against both of '
          'Spell::EffectWeaponDmg\'s Druid-specific special cases - matches neither, so no behavior needed porting. The stun aura (eff2) and '
          'its "lasts longer per combo point" tooltip claim are untouched and out of scope here - found no script anywhere keyed to this '
          'spell\'s id that actually scales the aura\'s DurationIndex=187 by combo points, so that claim may already be purely cosmetic/stock '
          'tooltip text with no live effect; flagging it, not fixing it, since it is a pre-existing question unrelated to this effect\'s own '
          'damage potency.',
    raw_overrides={'AttributesEx': 5505024, 'AttributesEx4': 8388608, 'AttributesEx7': 2048, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Stunned.', 'BaseLevel': 62, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Finishing move that causes damage and stuns the target.  Non-player victim spellcasting is also interrupted for $32747d.  Causes more damage and lasts longer per combo point:\r\n   1 point  : ${$b1*1+$m1+$mw}-${$b1*1+$M1+$MW} damage, 1 sec\r\n   2 points: ${$b1*2+$m1+$mw}-${$b1*2+$M1+$MW} damage, 2 sec\r\n   3 points: ${$b1*3+$m1+$mw}-${$b1*3+$M1+$MW} damage, 3 sec\r\n   4 points: ${$b1*4+$m1+$mw}-${$b1*4+$M1+$MW} damage, 4 sec\r\n   5 points: ${$b1*5+$m1+$mw}-${$b1*5+$M1+$MW} damage, 5 sec', 'DurationIndex': 187, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 1, 'SpellClassMask_2': 128, 'SpellClassSet': 7, 'SpellLevel': 62, 'SpellVisualID_1': 8148, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


barkskin_22812 = spell(
    id=22812,
    name='Barkskin',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=149, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=50411),
    ],
    spell_icon_id=689,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx5': 131080, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'All damage taken is reduced by $s2%.  While protected, damaging attacks will not cause spellcasting delays.', 'BaseLevel': 44, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "The druid's skin becomes as tough as bark.  All damage taken is reduced by $s2%.  While protected, damaging attacks will not cause spellcasting delays.  This spell is usable while stunned, frozen, incapacitated, feared or asleep.  Usable in all forms.  Lasts $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskC_1': 16777829, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcTypeMask': 40, 'RangeIndex': 1, 'SpellClassMask_2': 262144, 'SpellClassSet': 7, 'SpellLevel': 44, 'SpellVisualID_1': 6662},
)


frenzied_regeneration_22842 = spell(
    id=22842,
    name='Frenzied Regeneration',
    school=School.NORMAL,
    attributes=262160,
    category=1011,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=60000,
    power_type=PowerType.RAGE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.HEAL_PCT, base_points=29, implicit_target_a=1),
    ],
    spell_icon_id=50,
    notes="druid-rework FERAL §5: rage-to-health channel -> instant HEAL_PCT 30% of max health on self; eff1/eff2 removed, duration 0 (DurationIndex 0), cooldown and category cooldown 180 -> 60 sec (Cooldown Haste applies). Heart of the Wild's Mastery bonus comes from spell_dru_frenzied_regeneration_feral (stock AuraScript unbound).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'BaseLevel': 36, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly heals you for $s1% of your maximum health.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 144, 'SpellClassMask_2': 1073741824, 'SpellClassSet': 7, 'SpellLevel': 36, 'SpellVisualID_1': 249, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'DurationIndex': 0},
)


healing_touch_25297 = spell(
    id=25297,
    name='Healing Touch',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=33,
    range_yards=40.0,
    effects=[
        Effect(
            type=EffectType.HEAL, base_points=1943, points_per_level=6.199999809265137, die_sides=351, implicit_target_a=21,
            potency_excluded="superseded rank, kept only because an item_template row casts this exact "
            "spell id (see this spell's notes=) - potency forces MaxLevel=0 (uncapped) for the whole "
            "spell, which would silently remove this rank's historical MaxLevel=65 power ceiling. Same "
            "category as the Warlock pilot's Immolate Rank 3/8 exclusions (potency-system.PROGRESS.md "
            "P4); conservative default per P5 - exclude, keep as-is.",
        ),
    ],
    spell_icon_id=962,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid). Potency system P5 (druid pass): NOT converted - MaxLevel=65 is this rank\'s own historical power cap, and potency forces MaxLevel=0 spell-wide; conservative default (P4 precedent) is to exclude and keep this rank exactly as-is rather than uncap it.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals a friendly target for $<min> to $<max>.', 'EffectBonusMultiplier_1': 1.6100000143051147, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 65, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 11', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 1073741824, 'SpellClassMask_1': 32, 'SpellClassSet': 7, 'SpellDescriptionVariableID': 28, 'SpellLevel': 60, 'SpellVisualID_1': 58, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


starfire_25298 = spell(
    id=25298,
    name='Starfire',
    school=School.ARCANE,
    attributes=65536,
    cast_time_ms=3500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=16,
    range_yards=30.0,
    effects=[
        Effect(
            type=EffectType.SCHOOL_DAMAGE, base_points=692, points_per_level=3.0999999046325684, die_sides=125, implicit_target_a=6,
            potency_excluded="superseded rank, kept only because an item_template row casts this exact "
            "spell id (see this spell's notes=) - potency forces MaxLevel=0 (uncapped) for the whole "
            "spell, which would silently remove this rank's historical MaxLevel=66 power ceiling. Same "
            "category as the Warlock pilot's Shadow Bolt Rank 10 exclusion (potency-system.PROGRESS.md "
            "P4); conservative default per P5 - exclude, keep as-is.",
        ),
    ],
    spell_icon_id=1485,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid). Potency system P5 (druid pass): NOT converted - MaxLevel=66 is this rank\'s own historical power cap, and potency forces MaxLevel=0 spell-wide; conservative default (P4 precedent) is to exclude and keep this rank exactly as-is rather than uncap it.',
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 22, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes $s1 Arcane damage to the target.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 66, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 7', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 2, 'ShapeshiftMask': 1073741824, 'SpellClassMask_1': 4, 'SpellClassSet': 7, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 1264, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


rejuvenation_25299 = spell(
    id=25299,
    name='Rejuvenation',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=18,
    range_yards=40.0,
    duration_ms=15000,
    effects=[
        Effect(
            type=EffectType.APPLY_AURA, base_points=221, implicit_target_a=21, apply_aura=AuraType.PERIODIC_HEAL, amplitude=3000,
            potency_excluded="superseded rank, kept only because an item_template row casts this exact "
            "spell id (see this spell's notes=) - potency forces MaxLevel=0 (uncapped) for the whole "
            "spell, which would silently remove this rank's historical MaxLevel=65 power ceiling. Same "
            "category as the Warlock pilot's Corruption rank exclusion (potency-system.PROGRESS.md P4); "
            "conservative default per P5 - exclude, keep as-is.",
        ),
    ],
    spell_icon_id=64,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid). Potency system P5 (druid pass): NOT converted - MaxLevel=65 is this rank\'s own historical power cap, and potency forces MaxLevel=0 spell-wide; conservative default (P4 precedent) is to exclude and keep this rank exactly as-is rather than uncap it.',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx3': 128, 'AttributesEx4': 1048576, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Heals $s1 damage every $t1 seconds.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals the target for ${$m1*5*$<mult>} over $d.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 0.37599998712539673, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 65, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 11', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 1073741824, 'ShapeshiftMask': 2, 'SpellClassMask_1': 16, 'SpellClassSet': 7, 'SpellDescriptionVariableID': 176, 'SpellLevel': 60, 'SpellVisualID_1': 32, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


gift_of_the_wild_26991 = spell(
    id=26991,
    name='Gift of the Wild',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=64,
    range_yards=40.0,
    duration_ms=3600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=339, implicit_target_a=56, apply_aura=22, misc_value=1, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=13, implicit_target_a=56, apply_aura=AuraType.MOD_STAT, misc_value=-1, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=56, apply_aura=143, misc_value=126, radius_yards=100.0),
    ],
    spell_icon_id=2435,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid)',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases armor by $s1, all attributes by $s2 and all resistances by $s3.', 'BaseLevel': 70, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives the Gift of the Wild to all party and raid members, increasing armor by $s1, all attributes by $s2 and all resistances by $s3 for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 22148, 'SpellClassMask_1': 262144, 'SpellClassSet': 7, 'SpellLevel': 70, 'SpellPriority': 50, 'SpellVisualID_1': 212, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


innervate_29166 = spell(
    id=29166,
    name='Innervate',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=224, implicit_target_a=21, apply_aura=AuraType.PERIODIC_ENERGIZE, amplitude=1000),
    ],
    spell_icon_id=62,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx7': 65536, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Regenerating mana.', 'BaseLevel': 40, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Causes the target to regenerate mana equal to $s1% of the casting Druid's base mana pool over $d.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 1073741826, 'SpellClassMask_2': 4096, 'SpellClassSet': 7, 'SpellLevel': 40, 'SpellVisualID_1': 3884, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


ferocious_bite_31018 = spell(
    id=31018,
    name='Ferocious Bite',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=35,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=51, die_sides=61, implicit_target_a=6),
    ],
    spell_icon_id=1680,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid)',
    raw_overrides={'AttributesEx': 1049088, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Finishing move that causes damage per combo point and converts each extra point of energy (up to a maximum of $s2 extra energy) into ${$f1+$AP/410}.1 additional damage.  Damage is increased by your attack power.\r\n   1 point  : ${$m1+$b1*1+0.07*$AP}-${$M1+$b1*1+0.07*$AP} damage\r\n   2 points: ${$m1+$b1*2+0.14*$AP}-${$M1+$b1*2+0.14*$AP} damage\r\n   3 points: ${$m1+$b1*3+0.21*$AP}-${$M1+$b1*3+0.21*$AP} damage\r\n   4 points: ${$m1+$b1*4+0.28*$AP}-${$M1+$b1*4+0.28*$AP} damage\r\n   5 points: ${$m1+$b1*5+0.35*$AP}-${$M1+$b1*5+0.35*$AP} damage', 'EffectBasePoints_2': 29, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 2.0999999046325684, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectPointsPerCombo_1': 147.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'RangeIndex': 2, 'ShapeshiftMask': 1, 'SpellClassMask_1': 8388608, 'SpellClassSet': 7, 'SpellLevel': 60, 'SpellVisualID_1': 6587, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


cower_31709 = spell(
    id=31709,
    name='Cower',
    school=School.NORMAL,
    attributes=262160,
    category=84,
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
    spell_icon_id=958,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid)',
    raw_overrides={'AttributesEx': 134217728, 'AttributesEx2': 67108864, 'AttributesEx3': 65536, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Cower, causing no damage but lowering your threat a large amount, making the enemy less likely to attack you.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 70, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 1, 'SpellClassMask_2': 536870912, 'SpellClassSet': 7, 'SpellLevel': 60, 'SpellVisualID_1': 3883, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


lacerate_33745 = spell(
    id=33745,
    name='Lacerate',
    school=School.NORMAL,
    attributes=16,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=100,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, ap_potency=2.75, potency_kind='periodic', mechanic=15, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=22.37, potency_kind='direct', implicit_target_a=6),
    ],
    spell_icon_id=2246,
    notes=(
        "druid-rework FERAL §5: CumulativeAura 5 -> 3, cost 15 -> 10 rage, BaseLevel/SpellLevel 66 -> "
        "20 (trainer 216 level 20); spell_dru_lacerate (Flesh Render). potency-system (PLAN P6 step "
        "5, Feral pass): both effects are ap-only (old coefficients 0/0.010 periodic, 0/0.040 "
        "direct, via the hand-written bonus_coefficients() below, now removed) - ap_potency=8.6 "
        "(periodic tick) and 69.9 (direct hit) are druid-potency-report.md's base-implied defaults, "
        "matching the established P5 convention for a mismatched ap-only row; AP coefficients move "
        "0.010 -> 0.074 (periodic) and 0.040 -> 0.300 (direct), base V60s essentially unchanged by "
        "construction."
        ' Effect 1 (periodic) ap_potency 8.6 -> 3.44, effect 2 (direct) ap_potency 69.9 -> 27.96 (2026-10-08, DPS balance pass, user ruling: Bear DPS Lacerate x0.40).'
        ' Effect 1 (periodic) ap_potency 3.44 -> 2.75, effect 2 (direct) ap_potency 27.96 -> 22.37 (2026-10-08, DPS balance pass, user ruling: Bear DPS Lacerate x0.80, round 9).'
    ),
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 128, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '{pot1} damage every $t sec', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'CumulativeAura': 3, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Lacerates the enemy target, dealing {pot2} damage and making them bleed for {pot1.total} damage over $d and causing a high amount of threat.  This effect stacks up to $u times on the same target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 144, 'SpellClassMask_2': 256, 'SpellClassSet': 7, 'SpellLevel': 20, 'SpellVisualID_1': 8146, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
# druid-rework FERAL §5 / §0.1: learned at 20 on the live druid trainer 216 (the stock row sits on the dead
# trainer 33 at 66; mod-progression phase_07 re-inserts (216, 33745) at 66 - known WP-T limitation).
trained_by(lacerate_33745, trainer_id=216, req_level=20, money_cost=2000)
scripted_by(lacerate_33745, 'spell_dru_lacerate')  # Flesh Render's extra application


lifebloom_33763 = spell(
    id=33763,
    name='Lifebloom',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=14,
    range_yards=40.0,
    duration_ms=7000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, sp_potency=5.7, potency_kind='heal_periodic', implicit_target_a=21, apply_aura=AuraType.PERIODIC_HEAL, amplitude=1000),
        # Potency system P5 follow-up (2026-10-01): this DUMMY slot's own base_points/points_per_level
        # (252/9.7) are now VESTIGIAL - kept only because Druid::TriggerLifebloomBloom's
        # AfterEffectRemove/AfterDispel hooks are registered against EFFECT_1/SPELL_AURA_DUMMY and need
        # a real effect of that shape to bind to; its value is no longer read for the heal amount.
        # 33778 (the "bloom", previously an undeclared stock spell relayed into via CastCustomSpell) is
        # now a real potency-driven spell() of its own (lifebloom_bloom_33778, below) - TriggerLifebloomBloom
        # was changed to read 33778's own CalcValue() instead of this slot's GetAmount(). See that
        # declaration's notes for the full trace/design.
        Effect(type=EffectType.APPLY_AURA, base_points=252, points_per_level=9.7, implicit_target_a=21, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2101,
    notes="druid-rework RESTO §7: mana_cost_pct 28->14; BaseLevel/SpellLevel 64->26; re-anchored level recipe (Q19, proportional to the existing L80 values: tick 40/46/53 at 60/70/80, bloom 582/679/776) - stored/ppl per RESTO §7's table (tick bp=17 ppl=0.6625, bloom bp=252 ppl=9.7); tooltip drops the mana-return mention and states the one-target rule (mana return removed in spell_dru_lifebloom, WP-B; the second Lifebloom removal itself is Druid::OnLifebloomApplied, WP-B). Potency system P5 (druid pass): eff1 (the tick) converted to sp_potency=5.7 (potency-report default, base/coef already agreed). Potency system P5 follow-up: eff2 (the bloom-on-fall-off base) is now vestigial - the real bloom heal is declared on 33778 itself (lifebloom_bloom_33778, below); this slot's own base_points/ppl are dead data, kept only for the AfterRemove/AfterDispel hook's structural requirement. Tooltip's old self-reference ($s2) repointed to the real source ($33778s1).",
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx3': 128, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Heals {pot1} every second and $s2 when effect finishes or is dispelled.', 'BaseLevel': 26, 'CastingTimeIndex': 1, 'CumulativeAura': 3, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals the target for {pot1.total} over $d.  When Lifebloom completes its duration or is dispelled, the target instantly heals themself for $33778s1.  This effect can stack up to $u times on the same target.  May be active on one target at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 0, 'ShapeshiftMask': 2, 'SpellClassMask_2': 16, 'SpellClassSet': 7, 'SpellDescriptionVariableID': 176, 'SpellLevel': 26, 'SpellVisualID_1': 8145, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},  # ShapeshiftExclude Moonkin bit dropped - PLAN §11.5 / code review finding #7
)
trained_by(lifebloom_33763, trainer_id=216, req_level=26, money_cost=5000)


lifebloom_bloom_33778 = spell(
    id=33778,
    name='Lifebloom',
    school=School.NATURE,
    # Stock attributes (150994944 = SPELL_ATTR0_ALLOW_WHILE_MOUNTED | SPELL_ATTR0_ALLOW_WHILE_SITTING),
    # deliberately NOT the usual 65536/SPELL_ATTR0_NOT_SHAPESHIFTED every other declared spell here
    # uses - this spell is always force-cast by Druid::TriggerLifebloomBloom (DruidMechanics.cpp) when
    # Lifebloom falls off or is dispelled, and must never fail because the target happens to be
    # mounted or sitting at that moment.
    attributes=150994944,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.HEAL, sp_potency=81.3, base_potency=54.9, potency_kind='heal', implicit_target_a=1),
    ],
    spell_icon_id=962,
    notes="Potency system P5 follow-up (2026-10-01): promoted out of source/spells/npc.csv's inert "
          "reference-only bucket into a real, actively-generated declaration (was previously "
          "'pulled from existing data', never regenerated). This is Lifebloom's (33763) burst "
          "'bloom' heal, fired by Druid::TriggerLifebloomBloom (DruidMechanics.cpp) when Lifebloom "
          "falls off or is dispelled - traced in full before converting: TriggerLifebloomBloom used "
          "to read a FLAT, unscaled base value from 33763's own eff2 DUMMY slot "
          "(bloomEffect->GetAmount(), base_points=252/ppl=9.7, no SP applied), then separately called "
          "caster->SpellHealingBonusDone(target, finalHeal=33778, ...) to apply SP bonus using "
          "33778's OWN coefficient - sourced from a stock spell_bonus_data row "
          "(33778, direct_bonus=0.655, 'Druid - Lifebloom DH'), not the DBC itself (whose own "
          "EffectBonusMultiplier was 0.0). Base (on 33763) and coefficient (on 33778) were split "
          "across two different spells, which doesn't fit potency's one-effect/one-value model, so "
          "both numbers are now reproduced on THIS spell's own single effect instead: base_potency=54.9 "
          "reproduces the real pre-SP level-60 value (582, from the rework's own re-anchored level "
          "recipe) exactly; sp_potency=81.3 reproduces the real coefficient (0.655) exactly - the two "
          "disagree by ~48% as a single potency value (54.9 alone gives 0.44 coefficient, 81.3 alone "
          "overshoots the base to 861 @ 60), the same kind of independently-tuned-numbers mismatch "
          "seen elsewhere this project, resolved here via base_potency since both real numbers were "
          "worth keeping exactly rather than picking one. SpellLevel=26 (not this spell's own stock "
          "64) matches Lifebloom's own re-anchored learn level - CalcValue() clamps any caster below "
          "BaseLevel up to BaseLevel before scaling, so leaving SpellLevel at 64 would have frozen "
          "every sub-64 Druid's bloom at its flat base with zero level scaling, a real regression. "
          "unbind_bonus_coefficients() below retires the stock spell_bonus_data row so the generated "
          "EffectBonusMultiplier_1 actually takes effect (D1: a live spell_bonus_data row always wins "
          "over the DBC field). TriggerLifebloomBloom's C++ was updated to read this spell's own "
          "CalcValue() instead of 33763's DUMMY slot, and to pass EFFECT_0 (not the old EFFECT_1) to "
          "SpellHealingBonusDone, matching this spell's real (and only) effect index - see "
          "DruidMechanics.cpp. The ×stack and ×Harmony multipliers TriggerLifebloomBloom applies on "
          "top are untouched by any of this (they're applied after SpellHealingBonusDone returns, "
          "same as before). 33763's own eff2 DUMMY slot is now vestigial - see its own updated notes.",
    raw_overrides={'AttributesEx': 1056, 'AttributesEx2': 268451840, 'AttributesEx3': 65536, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals the target over 7 sec.  When Lifebloom completes its duration or is dispelled, the target instantly heals themself.  This effect can stack up to 3 times on the same target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 5, 'ShapeshiftExclude': 1073741824, 'SpellClassSet': 7, 'SpellLevel': 26, 'SpellVisualID_1': 8101, 'TargetCreatureType': 767},
)
unbind_bonus_coefficients(lifebloom_bloom_33778)


cyclone_33786 = spell(
    id=33786,
    name='Cyclone',
    school=School.NATURE,
    mechanic=Mechanic.BANISH,
    attributes=65536,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=20.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=39, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=6, apply_aura=AuraType.MOD_HEALING_PCT, misc_value=127),
    ],
    spell_icon_id=174,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 65536, 'AttributesEx4': 536872960, 'AttributesEx5': 32, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Invulnerable, but unable to act.', 'BaseLevel': 70, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Tosses the enemy target into the air, preventing all action but making them invulnerable for up to $d.  Only one target can be affected by your Cyclone at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 0, 'SpellClassMask_2': 32, 'SpellClassSet': 7, 'SpellLevel': 70, 'SpellVisualID_1': 8206, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


mangle_cat_33876 = spell(
    id=33876,
    name='Mangle (Cat)',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=45,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=60000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=99.1, potency_kind='direct', implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=6, apply_aura=255, misc_value=15),
        Effect(type=EffectType.ADD_COMBO_POINTS, implicit_target_a=6),
    ],
    spell_icon_id=2312,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 50); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80; learn level 50 -> 20 (trainer 216) re-anchored per PLAN B3 so level 80 keeps its flat bonus (99 + 6.133/level from 50 = 283): ppl 283/80 = 3.5375, bp 3.5375 x 20 - 1 ~= 70 (71 at 20, 177 at 50, 283 at 80). '
          'potency-system (P6 step 5 follow-up, 2026-10-01, REVISED): moved off the weapon-damage effects entirely (user call) rather than the '
          'weapon_potency fix from earlier this session - eff1 (flat WEAPON_DAMAGE, ~283 at 80) and the old eff3 (WEAPON_PERCENT_DAMAGE, already '
          'fixed to weapon_potency=199 earlier this session) are now one SCHOOL_DAMAGE effect, ap_potency=99.1, exactly reproducing the old '
          'total (689.4 at level 60/1000 AP). Mangle (Cat) also relied on Spell::EffectWeaponDmg\'s own "Mangle (Cat): CP" special case '
          '(SpellFamilyFlags[1]&0x400, a hard-coded AddComboPointGain(target,1) call) for its combo point - that only fires for weapon-type '
          'effects, so moving off them would have silently dropped it. Rather than porting the hard-coded call, added a plain '
          'EffectType.ADD_COMBO_POINTS effect instead (eff3) - functionally identical (Spell::EffectAddComboPoints also just calls '
          'AddComboPointGain, with its own CalcValue, defaulting to 1 via the same die_sides=1 "+1" roll every potency effect already relies '
          'on), and no core C++ edit needed. Mangle (Bear) does not award combo points (its own SpellFamilyFlags don\'t match this case) so '
          'doesn\'t need this addition - see its own declaration.',
    raw_overrides={'AttributesEx': 134218240, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'All bleed effects cause $s2% additional damage.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Mangle the target for {pot1} damage and causes the target to take $s2% additional damage from bleed effects for $d.  Awards $s3 combo $lpoint:points;.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 1, 'SpellClassMask_2': 1024, 'SpellClassSet': 7, 'SpellLevel': 20, 'SpellVisualID_1': 8634, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)
trained_by(mangle_cat_33876, trainer_id=216, req_level=20, money_cost=2000)  # druid-rework FERAL §5: talent -> baseline


mangle_bear_33878 = spell(
    id=33878,
    name='Mangle (Bear)',
    school=School.NORMAL,
    attributes=262160,
    category=971,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=6000,
    power_type=PowerType.RAGE,
    mana_cost=200,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=60000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=62.64, potency_kind='direct', implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=6, apply_aura=255, misc_value=15),
    ],
    spell_icon_id=2312,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 50); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80; druid-rework FERAL §5: now baseline (trainer 216 level 50), ShapeshiftMask 128 -> 144 (both bears), eff0 WEAPON_DAMAGE -> NORMALIZED_WEAPON_DMG keeping 74 / 6.1667; learn level 50 -> 10 (trainer 216) re-anchored per PLAN B3 so level 80 keeps its flat bonus (75 + 6.167/level from 50 = 260): ppl 260/80 = 3.25, bp 3.25 x 10 - 1 ~= 31 (32 at 10, 162 at 50, 260 at 80). '
          'potency-system (P6 step 5 follow-up, 2026-10-01, REVISED): moved off the weapon-damage effects entirely (user call), same treatment '
          'as Mangle (Cat) - eff1 (flat NORMALIZED_WEAPON_DMG, ~260 at 80) and the old eff3 (WEAPON_PERCENT_DAMAGE, already fixed to '
          'weapon_potency=114 earlier this session) are now one SCHOOL_DAMAGE effect, ap_potency=104.4, exactly reproducing the old total '
          '(726.9 at level 60/1000 AP, using the normalized-weapon-type (2H) raw roll - Bear Form abilities use the weapon-type-based speed '
          'constant, not the form\'s own swing timer, for a normalized effect). Unlike Mangle (Cat), this one does not award combo points '
          '(Bear Form has none) - its own SpellFamilyFlags (SpellClassMask_2=64) don\'t match Spell::EffectWeaponDmg\'s "Mangle (Cat): CP" '
          'check (flags[1]&0x400), check, confirmed before concluding no addition was needed here.'
          ' Effect 1 ap_potency 104.4 -> 62.64 (2026-10-08, DPS balance pass, user ruling: Bear DPS Mangle (Bear) x0.60).',
    raw_overrides={'AttributesEx': 134218240, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'All bleed effects cause $s2% additional damage.', 'BaseLevel': 10, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Mangle the target for {pot1} damage and causes the target to take $s2% additional damage from bleed effects for $d.  While Bestial Fury is active, has a 15% chance to grant Tooth and Claw.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': SS_ANY_BEAR, 'SpellClassMask_2': 64, 'SpellClassSet': 7, 'SpellLevel': 10, 'SpellVisualID_1': 6586, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
trained_by(mangle_bear_33878, trainer_id=216, req_level=10, money_cost=600)  # druid-rework FERAL §5: talent -> baseline


flight_form_33943 = spell(
    id=33943,
    name='Flight Form',
    school=School.NORMAL,
    attributes=268795920,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=13,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=36, misc_value=29),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=17),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=201),
    ],
    spell_icon_id=2274,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 60); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 2 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'ActiveIconID': 122, 'AttributesEx': 98304, 'AttributesEx4': 603979776, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Immune to Polymorph effects.\r\nMovement speed increased by $33948s2% and allows you to fly.', 'AuraInterruptFlags': 128, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shapeshift into flight form, increasing movement speed by $33948s2% and allowing you to fly.  Cannot use in combat.  Can only use this form in Outland or Northrend.\r\n\r\nThe act of shapeshifting frees the caster of Polymorph and Movement Impairing effects.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 14, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 1073741826, 'SpellClassMask_2': 32768, 'SpellClassSet': 7, 'SpellLevel': 60, 'SpellVisualID_1': 8128, 'StanceBarOrder': 5, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


swift_flight_form_40120 = spell(
    id=40120,
    name='Swift Flight Form',
    school=School.NORMAL,
    attributes=268795920,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=13,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=36, misc_value=27),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=17),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=201),
    ],
    spell_icon_id=2274,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by quest_template reward/display spell)',
    raw_overrides={'ActiveIconID': 122, 'AttributesEx': 98304, 'AttributesEx4': 603979776, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Immune to Polymorph effects.\r\nMovement speed increased by $40121s2% and allows you to fly.', 'AuraInterruptFlags': 128, 'BaseLevel': 70, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shapeshift into swift flight form, increasing movement speed by $40121s2% and allowing you to fly.  Cannot use in combat.  Can only use this form in Outland or Northrend.\r\n\r\nThe act of shapeshifting frees the caster of Polymorph and Movement Impairing effects.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 14, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Shapeshift', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 1073741826, 'SpellClassMask_2': 32768, 'SpellClassSet': 7, 'SpellLevel': 70, 'SpellVisualID_1': 8128, 'StanceBarOrder': 5, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


nourish_50464 = spell(
    id=50464,
    name='Nourish',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=18,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, sp_potency=192.1, potency_kind='heal', implicit_target_a=21),
    ],
    spell_icon_id=2863,
    notes='pulled from existing data. Potency system P5 (druid pass): converted to sp_potency=192.1 (potency-report default, base/coef already agreed).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 80, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals a friendly target for {pot1}. Heals for an additional 20% if you have a Rejuvenation, Regrowth, Lifebloom, or Wild Growth effect active on the target.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 85, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 1073741981, 'SpellClassMask_2': 33554432, 'SpellClassSet': 7, 'SpellLevel': 80, 'SpellVisualID_1': 11570, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
unbind_bonus_coefficients(nourish_50464)  # stale spell_bonus_data row overrode the potency coefficient (D1)


revive_50769 = spell(
    id=50769,
    name='Revive',
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
    spell_icon_id=2256,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 12); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 7 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 12, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Returns the spirit to the body, restoring a dead target to life with $s1 health and $q1 mana.  Cannot be cast when in combat.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 1073741824, 'SpellClassMask_3': 512, 'SpellClassSet': 7, 'SpellLevel': 12, 'SpellPriority': 50, 'SpellVisualID_1': 344, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Targets': 32768},
)
# Only on a stock TrainerId no NPC uses; 216 is the live Druid trainer (docs/spell_learn_level.md).
trained_by(revive_50769, trainer_id=216, req_level=12, money_cost=800)


savage_roar_52610 = spell(
    id=52610,
    name='Savage Roar',
    school=School.NORMAL,
    dispel=9,
    mechanic=31,
    attributes=537133072,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=25,
    mana_cost_pct=0,
    range_yards=100.0,
    duration_ms=9000,
    effects=[
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2865,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 4195328, 'AttributesEx2': 4, 'AttributesEx3': 1342439424, 'AttributesEx4': 16, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Physical damage done increased by $s2%.', 'AuraInterruptFlags': 4718592, 'BaseLevel': 75, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Finishing move that increases physical damage done by $s2%.  Only useable while in Cat Form.  Lasts longer per combo point:\r\n   1 point  : 14 seconds\r\n   2 points: 19 seconds\r\n   3 points: 24 seconds\r\n   4 points: 29 seconds\r\n   5 points: 34 seconds', 'DurationIndex': 581, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'SpellClassMask_2': 268435456, 'SpellClassSet': 7, 'SpellLevel': 75, 'SpellPriority': 50, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


swipe_cat_62078 = spell(
    id=62078,
    name='Swipe (Cat)',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=50,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=31, weapon_potency=249, implicit_target_a=6, chain_targets=1000),
    ],
    spell_icon_id=1562,
    notes=(
        "pulled from existing data. potency-system (PLAN P6 step 5, Feral pass): pure "
        "WEAPON_PERCENT_DAMAGE, no flat effect - converted to weapon_potency=249 (previously "
        "base_points=249 with the default die_sides=1, i.e. actually dealing 250% live - the same "
        "pre-existing off-by-one Mangle (Cat)/(Bear) had; weapon_potency's own -1/+1 convention "
        "lands on the intended 249%). No behavior change beyond that 1-point fix."
    ),
    raw_overrides={'AttributesEx': 512, 'AttributesEx2': 4096, 'AttributesEx5': 32768, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 71, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Swipe nearby enemies, inflicting $s1% weapon damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 1, 'SpellClassMask_3': 1024, 'SpellClassSet': 7, 'SpellLevel': 71, 'SpellVisualID_1': 13170, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


insect_swarm_5570 = spell(
    id=5570,
    name='Insect Swarm',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=30.0,
    duration_ms=14000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, sp_potency=17.3, potency_kind='periodic', implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=2000),
    ],
    spell_icon_id=1771,
    notes="pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->covers-60 (anchor rank 5 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80; druid-rework BALANCE §6 row (2,1): duration 12s->14s (7 ticks), hit-reduction eff2 dropped (12.12); scripted_by(spell_dru_insect_swarm_cast) removes the caster's Swarming Rot copy (200352) on a real cast. Potency system P5 (druid pass): converted to sp_potency=34.8 (not mismatched; potency-report base-damage default). mana_cost_pct 8 -> 6 (2026-10-08, DPS balance pass, user ruling: Balance mana). Effect 1 sp_potency 34.8 -> 20.9 (2026-10-08, DPS balance pass, user ruling: Balance damage -40%). Effect 1 sp_potency 20.9 -> 19.2 (2026-10-08, DPS balance pass, user ruling: Balance -8%). Effect 1 sp_potency 19.2 -> 17.3 (2026-10-08, DPS balance pass, user ruling: Balance -10%).",
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '{pot1} Nature damage every $t1 sec.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The enemy target is swarmed by insects, causing {pot1.total} Nature damage over $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 0, 'ShapeshiftMask': 1073741824, 'SpellClassMask_1': 2097152, 'SpellClassSet': 7, 'SpellLevel': 20, 'SpellVisualID_1': 7333, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


wild_growth_48438 = spell(
    id=48438,
    name='Wild Growth',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    category=1237,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=6000,
    mana_cost=0,
    mana_cost_pct=23,
    range_yards=40.0,
    duration_ms=7000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, sp_potency=13.9, potency_kind='heal_periodic', implicit_target_a=63, implicit_target_b=31, apply_aura=AuraType.PERIODIC_HEAL, amplitude=1000, radius_yards=15.0),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=87, implicit_target_b=31, apply_aura=AuraType.DUMMY, radius_yards=15.0),
    ],
    spell_icon_id=2864,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 60); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 4 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. Potency system P5 (druid pass): converted to sp_potency=13.9 (potency-report default, base/coef already agreed).',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx3': 128, 'AttributesEx4': 1048576, 'AttributesEx5': 4194304, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Heals {pot1} damage every $t1 second.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals up to $s3 friendly party or raid members within $a1 yards of the target for {pot1.total} over $d. The amount healed is applied quickly at first, and slows down as the Wild Growth reaches its full duration.', 'EffectBasePoints_3': 4, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_2': 67108864, 'SpellClassSet': 7, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 11568, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


starfall_48505 = spell(
    id=48505,
    name='Starfall',
    school=School.ARCANE | School.NATURE,  # Astral (druid-rework BALANCE §6 row 8,1)
    attributes=65536,
    category=1218,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=90000,
    mana_cost=0,
    mana_cost_pct=26,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=1000, trigger_spell=starfall_50286.id),
    ],
    spell_icon_id=2854,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 60); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 4 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. mana_cost_pct 35 -> 26 (2026-10-08, DPS balance pass, user ruling: Balance mana).',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx4': 64, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Summoning stars from the sky.', 'AuraInterruptFlags': 131072, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You summon a flurry of stars from the sky on all targets within $50286a yards of the caster, each dealing $50288s1 Arcane damage. Also causes $50294s1 Arcane damage to all other enemies within $50294a1 yards of the enemy target. Maximum 20 stars. Lasts $48505d.  Shapeshifting into an animal form or mounting cancels the effect. Any effect which causes you to lose control of your character will suppress the starfall effect.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 0.12700000405311584, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 2, 'ShapeshiftMask': 1073741824, 'SpellClassMask_2': 8388608, 'SpellClassSet': 7, 'SpellLevel': 60, 'SpellVisualID_1': 11571, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


typhoon_50516 = spell(
    id=50516,
    name='Typhoon',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    category=1217,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=20000,
    mana_cost=0,
    mana_cost_pct=25,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=89, radius_yards=30.0),
        Effect(type=EffectType.TRIGGER_SPELL, base_points=287, points_per_level=20.5, trigger_spell=typhoon_61391.id),
    ],
    spell_icon_id=2838,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 50); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80; druid-rework BALANCE §4 "Typhoon baseline at 36": BaseLevel/SpellLevel 50->36, eff2 base_points/points_per_level retuned so the level-36 floor matches the old level-50 floor (~1190 at 80); now trained (trained_by below), stock SLA 17467 (SkillLine 574) already files it under Balance',
    raw_overrides={'AttributesEx': 268435584, 'AttributesEx2': 524288, 'AttributesEx4': 1, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 36, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You summon a violent Typhoon that does $s2 Nature damage when in contact with hostile targets, knocking them back and dazing them for $61391d.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 2, 'ShapeshiftMask': 1073741824, 'Speed': 27.0, 'SpellClassMask_2': 16777216, 'SpellClassSet': 7, 'SpellLevel': 36, 'SpellMissileID': 1267, 'SpellVisualID_1': 9248, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Targets': 64},
)
trained_by(typhoon_50516, trainer_id=216, req_level=36, money_cost=11000)


natural_alacrity_17116 = spell(
    id=17116,
    name='Natural Alacrity',
    school=School.NORMAL,
    dispel=DispelType.MAGIC,
    attributes=327680,  # stock 33882112 minus SPELL_ATTR0_COOLDOWN_ON_EVENT - docs/bugs-and-fixes.md
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=108, misc_value=10),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=1, trigger_spell=200566),
    ],
    spell_icon_id=112,
    notes="druid-rework RESTO §7 'Natural Alacrity = 17116' (reuse of stock Nature's Swiftness, renamed baseline): cooldown 180000->60000; BaseLevel/SpellLevel 1->30; drop the Nourish bit from eff1's A_2 mask (33554464=0x2000020 -> 32=0x20, inert per the retired-bit rule); new eff2 TRIGGER_SPELL -> 200566 (the separate, non-consumed 10% healing buff); trained_by(216, req_level=30). Keeps the stock eff1 (SPELLMOD_CASTING_TIME -100%, 1 charge; the stock spell_proc 17116 row handles consumption).",
    raw_overrides={'AttributesEx': 131072, 'AttributesEx3': 196608, 'AttributesEx4': 64, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next Nature spell will be an instant cast spell. The effectiveness of your Nature healing spells is increased by 10% for 10 sec.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your next Druid Nature spell with a base cast time under 10 sec becomes instant. In addition, the effectiveness of your Nature healing spells is increased by 10% for 10 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 268436065, 'EffectSpellClassMaskA_2': 32, 'EffectSpellClassMaskA_3': 32768, 'EquippedItemClass': -1, 'InterruptFlags': 4, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'ShapeshiftExclude': 1073741824, 'SpellClassMask_2': 524288, 'SpellClassSet': 7, 'SpellLevel': 30, 'SpellPriority': 50, 'SpellVisualID_1': 4040},
)
trained_by(natural_alacrity_17116, trainer_id=216, req_level=30, money_cost=6000)


swiftmend_18562 = spell(
    id=18562,
    name='Swiftmend',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=25000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=16,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, sp_potency=56.6, potency_kind='heal', implicit_target_a=21),
    ],
    spell_icon_id=1917,
    notes="druid-rework RESTO §7/§8 (2,2): moved (6,1)->(2,2); no longer consumes a heal over time effect - extends Rejuvenation/Germination, Regrowth and Lifebloom by 6 sec instead (spell_dru_swiftmend, WP-B); cooldown 15000->25000 (below the Cooldown Haste floor); heal recipe v60=600 at learn level 19 (600/700/800 at 60/70/80, stored bp=189 ppl=10); TargetAuraState 15->0 (retires the core consume branch, CORE-AUDIT row 19); tooltip rewritten. Potency system P5 (druid pass): converted to sp_potency=56.6 (potency-report default, base/coef already agreed); the old bonus_coefficients(direct=1.4) spell_bonus_data override is retired in favor of the generated DBC coefficient.",
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712190, 'BaseLevel': 19, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Requires Rejuvenation, Regrowth or Lifebloom on the target. Heals the target for {pot1} and extends the duration of your Rejuvenation, Regrowth and Lifebloom on that target by 6 sec.  The extension may exceed their normal maximum duration.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 0, 'ShapeshiftMask': 2, 'SpellClassMask_2': 2, 'SpellClassSet': 7, 'SpellLevel': 19, 'SpellVisualID_1': 3884, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetAuraState': 0},  # ShapeshiftExclude Moonkin bit dropped - PLAN §11.5 / code review finding #7
)
scripted_by(swiftmend_18562, 'spell_dru_swiftmend')


moonkin_form_24858 = spell(
    id=24858,
    name='Moonkin Form',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=13,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=36, misc_value=31),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=17),
        Effect(type=EffectType.TRIGGER_SPELL, base_points=-1, implicit_target_a=1, trigger_spell=24907),
    ],
    spell_icon_id=111,
    notes='pulled from existing data',
    raw_overrides={'ActiveIconID': 122, 'AttributesEx': 98304, 'AttributesEx4': 2097152, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Immune to Polymorph effects.\r\nArmor contribution from items is increased by $24905s1%.\r\nDirect damage spells have a chance to instantly regenerate $53506s1% of your total mana.', 'BaseLevel': 40, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shapeshift into Moonkin Form.  While in this form the armor contribution from items is increased by $24905s1%, and all party and raid members within $24907a1 yards have their spell critical chance increased by $24907s1%.  Direct damage spells cast in this form have a $h% chance to instantly regenerate $53506s1% of your total mana.  The Moonkin can not cast healing or resurrection spells while shapeshifted.\r\n\r\nThe act of shapeshifting frees the caster of Polymorph and Movement Impairing effects.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Shapeshift', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 2, 'SpellClassMask_2': 8192, 'SpellClassSet': 7, 'SpellLevel': 40, 'SpellVisualID_1': 9302, 'StanceBarOrder': 4, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


force_of_nature_33831 = spell(
    id=33831,
    name='Force of Nature',
    school=School.NATURE,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=12,
    range_yards=30.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=2, implicit_target_a=8, misc_value=1964),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=16, apply_aura=226, amplitude=200, radius_yards=2.0),
    ],
    spell_icon_id=2258,
    notes='pulled from existing data; druid-rework BALANCE §6 row (4,1): cooldown 180s->120s, attributes/ShapeshiftMask cleared (usable in any form, spell_dru_force_of_nature blocks it with an active pet instead, WP-B)',
    raw_overrides={'AttributesEx': 268436480, 'AttributesEx2': 524288, 'AttributesEx3': 131072, 'AttributesEx6': 1024, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 50, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons $s1 treants to attack enemy targets for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 1562, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 512, 'SpellClassSet': 7, 'SpellLevel': 50, 'SpellVisualID_1': 8111, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Targets': 64},
)


berserk_50334 = spell(
    id=50334,
    name='Berserk',
    school=School.NORMAL,
    attributes=16,
    category=1208,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=180000,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=1, apply_aura=108, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=5),
    ],
    spell_icon_id=2852,
    notes="druid-rework FERAL §7 (10,1): 15 -> 10 sec, then 20 sec (post-addendum playtest); eff0 -50% cost now covers every Cat Form and Bear Form ability (BERSERK_COST, incl. Maul, Demoralizing Roar, Mangle (Bear), Lacerate, Swipe (Bear), Feral Charge (Bear), Ironfur, Pulverize, Upheaval, Thrash); eff1 Mangle (Bear) cooldown SpellMod -> APPLY_AURA DUMMY 2 (the Swell count Pulverize/Upheaval deal damage for, Druid::GetSwellStacksForDamage); eff2 fear immunity kept (stray classmasks on eff1/eff2 cleared); the 58923 'Mangle hits 3 targets' link is removed in druid_talents.py.",
    raw_overrides={'AttributesEx': 163872, 'AttributesEx5': 131072, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Cost of Cat Form and Bear Form abilities reduced by $s1%.  Immune to Fear effects.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "When activated, reduces the cost of all your Cat Form and Bear Form abilities by $s1%.  If Bestial Fury is active, grants $200426u stacks of Swell.  While active, your Pulverize and Upheaval consume no Swell and deal damage as though they consumed $s2, your Cat Form combo point generators grant 4 additional combo points, and your Savage Defense absorb effect is doubled.  Lasts $d.  You cannot use Tiger's Fury while Berserk is active.\r\n\r\nClears the effect of Fear and makes you immune to Fear for the duration.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': BERSERK_COST[0], 'EffectSpellClassMaskA_2': BERSERK_COST[1], 'EffectSpellClassMaskA_3': BERSERK_COST[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_3': 64, 'SpellClassSet': 7, 'SpellLevel': 60, 'SpellVisualID_1': 11566, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


survival_instincts_61336 = spell(
    id=61336,
    name='Survival Instincts',
    school=School.NORMAL,
    attributes=16,
    category=1251,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=180000,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=14),
    ],
    spell_icon_id=3707,
    notes="druid-rework FERAL §5 / §0.16: eff0 30 -> 20% max health; ShapeshiftMask 0 -> cat + form 8 (0x81), so it can't be cast in Bestial Fury and an active one ends on entering it (Stances drop the aura on a form change). Stock spell_dru_survival_instincts(_aura) stay bound.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': "Maximum health increased by $s1%.  Nurturing Instinct's increased healing received effect is tripled.", 'BaseLevel': 20, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your maximum health by $s1% and triples the effectiveness of Nurturing Instinct's increased healing received effect for $d.  Only usable while in Cat, Bear or Dire Bear Form.  Cannot be used while Bestial Fury is active.  After the effect expires, the health is lost.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8622080, 'EffectSpellClassMaskA_2': 805307520, 'EffectSpellClassMaskA_3': 32, 'EffectSpellClassMaskC_1': 2048, 'EffectSpellClassMaskC_2': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_3': 128, 'SpellClassSet': 7, 'SpellLevel': 20, 'SpellVisualID_1': 2758, 'ShapeshiftMask': SS_CAT | SS_BEAR},
)


# --- druid-rework Balance WP-A: new baseline/talent-granted castables (BALANCE.md §5) ---

starsurge_200333 = spell(
    id=200333,
    name='Starsurge',
    school=School.ARCANE | School.NATURE,  # Astral
    attributes=65536,  # NOT_SHAPESHIFTED
    cast_time_ms=0,
    cooldown_ms=10000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=74.4, potency_kind='direct', implicit_target_a=6),
    ],
    spell_icon_id=1957,
    notes='NEW (druid-rework BALANCE §5 "Starsurge"): scales with level (PLAN B3), learn level 22, level-60 value 200 -> ppl 200/60; on the Cooldown Haste allow list (A3); shares icon 1957 with Genesis talent (spell vs talent, accepted 12.14); a projectile at Speed 35 (Ice Lance is 38) with Ascension\'s own Starsurge missile/hand-flare/impact art, SpellVisualID_1 90018 (patch_druid_vfx_models.py), replacing the borrowed Starfire visual 1264. Potency system P5 (druid pass): converted to sp_potency=74.4 (potency-report default, base/coef already agreed); the old bonus_coefficients(direct=0.5) spell_bonus_data override is retired in favor of the generated DBC coefficient.',
    raw_overrides={'BaseLevel': 22, 'SpellLevel': 22, 'MaxLevel': 80, 'FacingCasterFlags': 1, 'PreventionType': 1, 'DefenseType': 1, 'ProcChance': 101, 'SpellClassSet': 7, 'SpellClassMask_3': STARSURGE, 'ShapeshiftMask': 1073741824, 'SpellVisualID_1': 90018, 'Speed': 35.0, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Launches a surge of stellar energies at the target, dealing {pot1} Astral damage.', 'EquippedItemClass': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)
trained_by(starsurge_200333, trainer_id=216, req_level=22, money_cost=3000)
skill_line_ability(id=30424, skill_line=574, spell_id=starsurge_200333.id, class_mask=1024)
scripted_by(starsurge_200333, 'spell_dru_starsurge')


mass_entanglement_200334 = spell(
    id=200334,
    name='Mass Entanglement',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    mechanic=Mechanic.ROOT,
    attributes=1073741824,  # Entangling Roots' 0x40010000 without NOT_SHAPESHIFTED
    cast_time_ms=0,
    cooldown_ms=40000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=30.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, mechanic=Mechanic.ROOT, implicit_target_a=53, implicit_target_b=16, apply_aura=AuraType.MOD_ROOT, radius_yards=8.0),
    ],
    spell_icon_id=90110,
    notes='NEW (druid-rework BALANCE §5 "Mass Entanglement"): usable in all forms (ShapeshiftMask 0); no target cap, 8yd radius (§0.13); icon 90110 mined (build_patch_i.py: spell_druid_massentanglement); damage-break flags copied from Entangling Roots 339; AttributesEx5 LIMIT_N (0x20) deliberately NOT copied — it makes the root single-target so each new victim strips it from the last',
    raw_overrides={'BaseLevel': 46, 'SpellLevel': 46, 'MaxLevel': 80, 'DefenseType': 1, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 664232, 'AttributesEx4': 536872960, 'AttributesEx6': 8388608, 'AuraInterruptFlags': 4718592, 'SpellClassSet': 7, 'SpellClassMask_3': MASS_ENTANGLEMENT, 'SpellVisualID_1': 38, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Roots the target and all enemies within $a1 yards in place for $d. Damage may interrupt the effect. Usable in all shapeshift forms.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Rooted.', 'EquippedItemClass': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)
trained_by(mass_entanglement_200334, trainer_id=216, req_level=46, money_cost=20000)
skill_line_ability(id=30425, skill_line=574, spell_id=mass_entanglement_200334.id, class_mask=1024)


solar_beam_200335 = spell(
    id=200335,
    name='Solar Beam',
    school=School.NATURE,
    attributes=65536,  # NOT_SHAPESHIFTED
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=30.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.INTERRUPT_CAST, implicit_target_a=6),
        Effect(type=EffectType.PERSISTENT_AREA_AURA, base_points=-1, mechanic=Mechanic.SILENCE, implicit_target_a=53, apply_aura=27, radius_yards=5.0),
    ],
    spell_icon_id=3769,
    notes='NEW (druid-rework BALANCE §5 "Solar Beam"): a dynamic-object persistent area aura, no creature needed; the DynObjAura re-evaluates units in range each update so only enemies standing in the beam are silenced',
    raw_overrides={'BaseLevel': 56, 'SpellLevel': 56, 'MaxLevel': 80, 'DefenseType': 1, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 7, 'ShapeshiftMask': 1073741824, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Summons a beam of solar light over an enemy target's location, interrupting the target and silencing all enemies within the beam. Lasts $d.", 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Silenced.', 'EquippedItemClass': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)
trained_by(solar_beam_200335, trainer_id=216, req_level=56, money_cost=30000)
skill_line_ability(id=30426, skill_line=574, spell_id=solar_beam_200335.id, class_mask=1024)


fury_of_elune_200336 = spell(
    id=200336,
    name='Fury of Elune',
    school=School.ARCANE | School.NATURE,  # Astral
    attributes=65536,  # NOT_SHAPESHIFTED
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=30.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=6, apply_aura=226, amplitude=500),
    ],
    spell_icon_id=90111,
    notes='NEW (druid-rework BALANCE §5 "Fury of Elune"), talent (10,1) on repurposed 1923: the aura sits on the target so the beam follows it for free; OnEffectPeriodic casts 200338/200339 each tick, OnCast casts 200340 Celestial Alignment and halves the running Starsurge cooldown (spell_dru_fury_of_elune, WP-B); icon 90111 mined (build_patch_i.py: ability_druid_cresentburn); SpellVisualID_1 90019 (patch_druid_vfx_models.py): the aura\'s StateKit carries Ascension\'s Fury of Elune beam model (cfx_druid_furyofelune_statebase) and looping beam sound on the target for the aura\'s duration',
    raw_overrides={'BaseLevel': 60, 'SpellLevel': 60, 'MaxLevel': 80, 'DefenseType': 1, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 7, 'ShapeshiftMask': 1073741824, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'SpellVisualID_1': 90019, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Calls down a beam of celestial energy that follows the target for $d, dealing $200338s1 Astral damage every 0.5 sec, and half that to other enemies within 8 yards. You also gain Celestial Alignment for 8 sec, granting the benefits of both Solar and Lunar Eclipse, with your Astral damage taking both bonuses, and halving the cooldown of Starsurge.', 'EquippedItemClass': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)
scripted_by(fury_of_elune_200336, 'spell_dru_fury_of_elune')


# Resto WP-0 pull (druid-rework.RESTO.md §3 item 1/§0.13 Q15): also present as a legacy row in
# source/spells/npc.csv - that row is deleted in this same change (generate.py rejects an id
# declared in both places). Resto's WP-A retunes duration/cooldown/cost and adds eff3 (the Tree of
# Life instant-Rejuvenation-heal %); CORE-AUDIT row 38 turns eff0 MOD_SHAPESHIFT into
# SPELL_AURA_TRANSFORM misc 21072 so this is a buff with the tree model, not a real form.
tree_of_life_33891 = spell(
    id=33891,
    name='Tree of Life',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=13,
    range_yards=0.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.TRANSFORM, misc_value=21072),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=17),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2257,
    notes="pulled from existing data; druid-rework RESTO §0.13 Q15 / CORE-AUDIT row 38: Tree of Life is a transform buff (SPELL_AURA_TRANSFORM misc 21072, the stock Living Grove Defender creature whose only model is display 864), not a shapeshift form - no cast restrictions while active. cooldown_ms 0->120000, duration_ms -1->20000 (was permanent-until-cancelled). New eff3 APPLY_AURA+DUMMY stored 24 (the Tree of Life instant-Rejuvenation-heal %, read by Druid::OnRejuvenationApplied via spell_dru_rejuvenation, WP-B). 5420's bonuses (HoT cost, Healing Touch cast time, Regrowth crit) ride along via linked_spell(33891, 5420, type=2) instead of ShapeshiftMask. 34123 (the +6% healing-received raid aura) is dropped (Q14) - not referenced by this tooltip. Code-review fix: eff3 was a plain SPELL_EFFECT_DUMMY effect, so GetAuraEffect(33891, EFFECT_2) always returned null and Tree of Life's instant Rejuvenation heal never fired. Tooltip's last line drops the stock 'Movement Impairing effects' claim: snares/roots are only cleared by HandleAuraModShapeshift's RemoveAurasByShapeShift, which a transform never reaches. Polymorph is still freed (eff2 MECHANIC_IMMUNITY 17 + SPELL_ATTR1_IMMUNITY_PURGES_EFFECT lets it cast while polymorphed and purges the polymorph).",
    raw_overrides={'AttributesEx': 98304, 'AttributesEx4': 2097152, 'CastingTimeIndex': 1, 'ProcTypeMask': 174624, 'ProcChance': 100, 'BaseLevel': 50, 'SpellLevel': 50, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 8598, 'ActiveIconID': 122, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': "Shift into the Tree of Life for $d. While active, the mana cost of your heal over time spells is reduced by 20%, your Rejuvenation instantly heals for 25% of its total healing when applied, your Wild Growth heals one additional target, your Healing Touch cast time is reduced by 50%, and your Regrowth's direct heal gains 25% additional critical heal chance.\n\nCasting Tree of Life frees the caster of Polymorph effects.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Immune to Polymorph effects.', 'AuraDescription_Lang_Mask': 16712190, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'SpellClassSet': 7, 'SpellClassMask_2': 65536, 'StanceBarOrder': 4, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


# ============================================================================
# druid-rework RESTO WP-A: new castable spells (RESTO §2.1, §6)
# ============================================================================

bloom_200560 = spell(
    id=200560,
    name='Bloom',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=90000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, sp_potency=23.6, potency_kind='heal', implicit_target_a=21),
    ],
    spell_icon_id=90130,
    notes="druid-rework RESTO §6 'Bloom (200560 castable, 200561 jump)': talent (6,1). Level recipe v60=250, learn level 39 (250/292/333 at 60/70/80, stored bp=162, ppl=4.16667). CheckCast requires the explicit target to carry the caster's Rejuvenation or Germination; AfterHit starts Druid::StartBloomJumps (0.3 s waves, up to 3 new targets each within 20 yd/LoS of the previous wave, lowest HP% first, no target cap, visited-once). Direct Nature healing spell. A lobbed projectile (Speed 25, SpellVisualID_1 90023 from patch_druid_vfx_models.py: green orb on a high parabola, stock Nourish flower on landing); AfterHit runs on landing, so the jumps start from there. Potency system P5 (druid pass): converted to sp_potency=23.6 (potency-report default, base/coef already agreed); the old bonus_coefficients(direct=0.75) spell_bonus_data override (and the redundant hand-set EffectBonusMultiplier_1) are retired in favor of the generated DBC coefficient.",
    raw_overrides={'BaseLevel': 39, 'SpellLevel': 39, 'MaxLevel': 80, 'DefenseType': 1, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 7, 'SpellClassMask_3': BLOOM, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals a friendly target affected by your Rejuvenation for {pot1}. After a short delay it jumps to 3 nearby allies affected by your Rejuvenation. This repeats until no valid targets remain in range. Each target can be healed only once per cast.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'SpellVisualID_1': 90023, 'Speed': 25.0},
)
scripted_by(bloom_200560, 'spell_dru_bloom')


cenarion_ward_200562 = spell(
    id=200562,
    name='Cenarion Ward',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=45000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=18,
    range_yards=40.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=21, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=198,
    notes="druid-rework RESTO §6 'Cenarion Ward (200562 ward, 200563 heal)': baseline, learned at 38 (Nourish's replacement, same cost). eff1 is a 1-charge DUMMY proc aura; procs_on(200562, PROC_FLAG_TAKEN_DAMAGE, chance=100) below covers melee/spell/periodic damage taken with no phase mask needed. spell_dru_cenarion_ward's OnEffectProc casts 200563 (preserving the druid as aura caster) and the ward is consumed. Not extended by Swiftmend; extended by Flourish only once released (200563 is the HoT, this isn't).",
    raw_overrides={'AttributesEx3': 2048, 'BaseLevel': 38, 'SpellLevel': 38, 'MaxLevel': 80, 'DefenseType': 1, 'PreventionType': 1, 'ProcChance': 101, 'ProcCharges': 1, 'SpellClassSet': 7, 'SpellClassMask_3': CENARION_WARD, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Protects a friendly target for $d. Any damage taken, including damage over time, consumes the ward and heals the target for $o1 over $200563d.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Protected by Cenarion Ward.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
trained_by(cenarion_ward_200562, trainer_id=216, req_level=38, money_cost=12000)
skill_line_ability(id=30446, skill_line=573, spell_id=cenarion_ward_200562.id, class_mask=1024)
scripted_by(cenarion_ward_200562, 'spell_dru_cenarion_ward')


flourish_200564 = spell(
    id=200564,
    name='Flourish',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=90000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=7999, implicit_target_a=1),
        Effect(type=EffectType.DUMMY, base_points=99, implicit_target_a=1),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=1, trigger_spell=flourish_buff_200565.id),
    ],
    spell_icon_id=90131,
    notes="druid-rework RESTO §6 'Flourish (200564 castable, 200565 buff)': talent (10,1). eff1 DUMMY stored 7999 (the 8 s extension), eff2 DUMMY stored 99 (+100% tick rate), eff3 triggers the 8 s visible buff. spell_dru_flourish extends (Druid::ExtendHot +8000) and accelerates (AuraEffect::AccelerateTicks) every heal over time effect the caster has within 60 yd, including Cultivation/Germination; OnAuraApply also gives a HoT newly applied during the buff's window the same treatment (Q16). SpellVisualID_1 90021 (patch_druid_vfx_models.py): stock nature cast hands + the stock Flourish burst and sound; the ground effect is flourish_ground_200603, triggered by the buff.",
    raw_overrides={'BaseLevel': 50, 'SpellLevel': 50, 'MaxLevel': 80, 'DefenseType': 1, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 7, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Extends the duration of all your heal over time effects on friendly targets within 60 yards by 8 sec and increases the tick rate of all your heal over time effects by 100% for 8 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'SpellVisualID_1': 90021},
)
scripted_by(flourish_200564, 'spell_dru_flourish', 'spell_dru_empowered_touch_capstone')


# --- druid-rework Feral pass WP-0 (FERAL §3 item 1 + §0.16): stock rows pulled verbatim with
# pull_dsl.py --constants. WP-A edits them; an untouched pulled row emits nothing.


feral_charge_bear_16979 = spell(
    id=16979,
    name='Feral Charge - Bear',
    school=School.NORMAL,
    attributes=537133072,
    category=1205,
    cast_time_ms=0,
    cooldown_ms=15000,
    category_cooldown_ms=15000,
    power_type=PowerType.RAGE,
    mana_cost=50,
    mana_cost_pct=0,
    range_yards=25.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.CHARGE, die_sides=0, implicit_target_a=6),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=6, trigger_spell=19675),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=6, trigger_spell=45334),
    ],
    spell_icon_id=1559,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx6': 8388608, 'AttributesEx7': 264192, 'ShapeshiftMask': 144, 'FacingCasterFlags': 1, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 20, 'SpellLevel': 20, 'RangeIndex': 95, 'EquippedItemClass': -1, 'SpellVisualID_1': 5162, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Causes you to charge an enemy, immobilizing and interrupting any spell being cast for $19675d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Immobilized.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 7, 'SpellClassMask_2': 1, 'SpellClassMask_3': 16, 'PreventionType': 2, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_2': 1.0},
)
trained_by(feral_charge_bear_16979, trainer_id=216, req_level=20, money_cost=2000)  # druid-rework FERAL §5: talent -> baseline (stock SLA 9464, SkillLine 134)


feral_charge_cat_49376 = spell(
    id=49376,
    name='Feral Charge - Cat',
    school=School.NORMAL,
    attributes=541327376,
    category=1205,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=15000,
    power_type=PowerType.ENERGY,
    mana_cost=10,
    mana_cost_pct=0,
    range_yards=25.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=6, trigger_spell=50259),
        Effect(type=42, die_sides=0, implicit_target_a=65, misc_value=5),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=87, trigger_spell=61138),
    ],
    spell_icon_id=3930,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 1056, 'AttributesEx2': 268435456, 'AttributesEx3': 65536, 'AttributesEx5': 1024, 'AttributesEx6': 8388612, 'ShapeshiftMask': 1, 'FacingCasterFlags': 1, 'ExcludeTargetAuraSpell': 65219, 'CastingTimeIndex': 1, 'InterruptFlags': 5, 'AuraInterruptFlags': 33554432, 'ProcChance': 101, 'BaseLevel': 20, 'SpellLevel': 20, 'RangeIndex': 95, 'EquippedItemClass': -1, 'EffectMultipleValue_2': 4.0, 'EffectMiscValueB_2': 150, 'SpellVisualID_1': 11039, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'Causes you to leap behind an enemy, dazing them for $50259d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Dazed.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 7, 'SpellClassMask_3': 32, 'PreventionType': 2, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0},
)
trained_by(feral_charge_cat_49376, trainer_id=216, req_level=20, money_cost=2000)  # druid-rework FERAL §5: talent -> baseline (stock SLA 17005, SkillLine 134)


dire_bear_form_9634 = spell(
    id=9634,
    name='Dire Bear Form',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=35,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MOD_SHAPESHIFT, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=17),
    ],
    spell_icon_id=107,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 98304, 'AttributesEx4': 2097152, 'ShapeshiftExclude': 1073741826, 'CastingTimeIndex': 1, 'ProcChance': 101, 'MaxLevel': 100, 'BaseLevel': 40, 'SpellLevel': 40, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 4227, 'ActiveIconID': 122, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Shapeshift', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shapeshift into dire bear form, increasing melee attack power by $9635s3, armor contribution from cloth and leather items by $9635s1%, and Stamina by $9635s2%.  Also protects the caster from Polymorph effects and allows the use of various bear abilities.\r\n\r\nThe act of shapeshifting frees the caster of Polymorph and Movement Impairing effects.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Immune to Polymorph effects.  Increases melee attack power by $9635s3, armor contribution from cloth and leather items by $9635s1%, and Stamina by $9635s2%.', 'AuraDescription_Lang_Mask': 16712190, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'SpellClassSet': 7, 'SpellClassMask_1': 1073741824, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


# ============================================================================
# druid-rework FERAL WP-A: new baseline bear abilities (FERAL §2/§4, WP-BRIEF §3) and Bestial Fury
# (talent 804, FERAL §0.16). Attacks copy Mangle (Bear)'s melee template (FERAL §4); spell visuals are
# borrowed from the closest stock ability (Balance precedent) - dedicated VFX is the planned follow-up.
# ============================================================================


def _feral_new_raw(desc, aura_desc=None, **extra):
    raw = {
        'CastingTimeIndex': 1, 'ProcChance': 101, 'SpellClassSet': 7, 'EquippedItemClass': -1,
        'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '',
        'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': desc,
        'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0,
    }
    if aura_desc is not None:
        raw['AuraDescription_Lang_Mask'] = 16712190
        raw['AuraDescription_Lang_enUS'] = aura_desc
    raw.update(extra)
    return raw


# Mangle (Bear) 33878's melee template (FERAL §4) - attacks only.
_BEAR_ATTACK_RAW = {
    'AttributesEx': 134218240, 'DefenseType': 2, 'PreventionType': 2, 'RangeIndex': 2, 'FacingCasterFlags': 1,
    'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'ShapeshiftMask': SS_ANY_BEAR,
}


ironfur_200420 = spell(
    id=200420,
    name='Ironfur',
    school=School.NORMAL,
    attributes=262160,  # IS_ABILITY | DO_NOT_SHEATH
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=200,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=AuraType.MOD_RESISTANCE_PCT, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=90120,
    notes="NEW (druid-rework FERAL §4 'Ironfur', WP-BRIEF §3): +8% armor per stack, 5 stacks sharing one 8 sec timer "
          "(stock CumulativeAura behaviour; the 'expiry drops one stack' part is spell_dru_ironfur's AuraScript). 20 "
          "rage, no cooldown, off the GCD (§0.16 Q4). ShapeshiftMask 0x80 = the everyday bear only, so it can't be cast "
          "in Bestial Fury and entering Bestial Fury drops it (§0.16). Self-buff, so it takes Enrage/Tiger's Fury's "
          "self-cast layout (RangeIndex 1, no DefenseType/facing) rather than Mangle's melee template. Visual: Barkskin's.",
    raw_overrides=_feral_new_raw(
        "Increases your armor by $s1% for $d, stacking up to $u times.  Each application resets the duration; when it "
        "expires, one stack is removed and the duration resets.  Cannot be used while Bestial Fury is active.",
        "Armor increased by $s1% per stack.",
        BaseLevel=20, SpellLevel=20, MaxLevel=80, RangeIndex=1, CumulativeAura=5, ShapeshiftMask=SS_BEAR,
        SpellClassMask_3=IRONFUR, StartRecoveryCategory=0, StartRecoveryTime=0, SpellVisualID_1=6662,
        EffectBonusMultiplier_1=1.0,
    ),
)
trained_by(ironfur_200420, trainer_id=216, req_level=20, money_cost=2000)
skill_line_ability(id=30434, skill_line=134, spell_id=ironfur_200420.id, class_mask=1024)
scripted_by(ironfur_200420, 'spell_dru_ironfur')


pulverize_200421 = spell(
    id=200421,
    name='Pulverize',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=250,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=42.54, potency_kind='direct', implicit_target_a=6),
        Effect(type=EffectType.DUMMY, base_points=19, implicit_target_a=6),
    ],
    spell_icon_id=102,
    notes="NEW (druid-rework FERAL §4 'Pulverize', §11.4, WP-BRIEF §3): physical SCHOOL_DAMAGE, not a weapon attack "
          "(60 + 5/level from level 22, ~350 at 80, +0.30 AP - 2.5x Upheaval, keeping Upheaval at 40% of Pulverize), "
          "eff1 20 = +% damage per Lacerate application consumed; spell_dru_pulverize requires 3 Lacerate "
          "stacks, multiplies by (1 + 0.20 x stacks) x (1 + 0.25 x Swell), then resets Lacerate to 1 and consumes up to 2 "
          "Swell. Learned at 22 (§13 Q11). Visual: Mangle (Bear)'s. potency-system (PLAN P6 step 5, Feral pass): "
          "eff0 is ap-only (old coefficient 0/0.30) - ap_potency=93.5 is druid-potency-report.md's base-implied "
          "default, matching the P5 convention; AP coefficient moves 0.30 -> 0.401, base V60 250 -> ~250 "
          "(essentially unchanged by construction). Upheaval/Thrash (structurally identical bear AoE abilities with "
          "the same bonus_coefficients(ap=...) pattern) were left unconverted - not named in this pass's scope, "
          "flagged for a follow-up."
          ' Effect 1 ap_potency 93.5 -> 65.45 (2026-10-08, DPS balance pass, user ruling: Bear DPS Pulverize x0.70).'
          ' Effect 1 ap_potency 65.45 -> 42.54 (2026-10-08, DPS balance pass, user ruling: Bear DPS Pulverize x0.65, round 9).',
    raw_overrides=_feral_new_raw(
        "Requires 3 applications of Lacerate on the target.  Deals {pot1} damage, increased by $s2% "
        "for each application of your Lacerate on the target, then consumes Lacerate and reapplies it with 1 "
        "application.  "
        "Consumes up to 2 stacks of Swell, increasing damage by 25% per stack consumed.",
        **_BEAR_ATTACK_RAW, BaseLevel=22, SpellLevel=22, MaxLevel=80, SpellClassMask_3=PULVERIZE,
        SpellVisualID_1=6586, DurationIndex=0,
    ),
)
trained_by(pulverize_200421, trainer_id=216, req_level=22, money_cost=3000)
skill_line_ability(id=30435, skill_line=134, spell_id=pulverize_200421.id, class_mask=1024)
scripted_by(pulverize_200421, 'spell_dru_pulverize')


upheaval_200422 = spell(
    id=200422,
    name='Upheaval',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=250,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=33.6, potency_kind='direct', implicit_target_a=22, implicit_target_b=15, radius_yards=8.0),
    ],
    spell_icon_id=66,
    notes="NEW (druid-rework FERAL §4 'Upheaval', §11.4, WP-BRIEF §3): physical SCHOOL_DAMAGE, not a weapon attack "
          "to up to 10 enemies within 8 yd; spell_dru_upheaval keeps the 10 closest, applies "
          "sqrt(5/N) past 5 and (1 + 0.25 x Swell), consumes up to 2 Swell once per cast. Upheaval-only family bit "
          "(reclaimed dword 3 0x20000, CORE-AUDIT row 23). Learned at 34. Visual: Swipe (Bear)'s. "
          "potency-system (PLAN P6 step 5 follow-up, 2026-10-01): ap-only (old coefficient 0/0.12, via the removed "
          "bonus_coefficients() below) - ap_potency=33.6 is druid-potency-report.md's base-implied default, matching "
          "the established P5/Feral convention; AP coefficient moves 0.12 -> 0.144, base V60 90 -> ~86 (essentially "
          "unchanged by construction). Same structural follow-up as Pulverize/Savage Bite/Lacerate, just not named in "
          "the original pass's scope.",
    raw_overrides=_feral_new_raw(
        "Slams the ground, dealing {pot1} damage to up to $i enemies within $a1 yards.  "
        "When more than 5 enemies are hit, the damage to each is reduced.  Consumes up to 2 stacks of Swell, increasing damage by 25% per "
        "stack consumed.",
        **_BEAR_ATTACK_RAW, BaseLevel=34, SpellLevel=34, MaxLevel=80, MaxTargets=10, SpellClassMask_3=UPHEAVAL,
        SpellVisualID_1=189, DurationIndex=0,
    ),
)
trained_by(upheaval_200422, trainer_id=216, req_level=34, money_cost=10000)
skill_line_ability(id=30436, skill_line=134, spell_id=upheaval_200422.id, class_mask=1024)
scripted_by(upheaval_200422, 'spell_dru_upheaval')


thrash_200423 = spell(
    id=200423,
    name='Thrash',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=6000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=200,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=12000,
    effects=[
        # All three effects share targets and radius so spell_dru_thrash's EFFECT_ALL target hook sees one list.
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=40.7, potency_kind='direct', implicit_target_a=22, implicit_target_b=15, radius_yards=10.0),
        Effect(type=EffectType.APPLY_AURA, ap_potency=6.7, potency_kind='periodic', mechanic=15, implicit_target_a=22, implicit_target_b=15, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000, radius_yards=10.0),
        Effect(type=EffectType.APPLY_AURA, base_points=-6, implicit_target_a=22, implicit_target_b=15, apply_aura=AuraType.MOD_RESISTANCE_PCT, misc_value=1, radius_yards=10.0),
    ],
    spell_icon_id=496,
    notes="NEW (druid-rework FERAL §4 'Thrash', §11.2, WP-BRIEF §3): one spell = 10 yd AoE hit + 12 sec bleed, 4 "
          "ticks + the -5% armor Faerie Fire (Feral) used to carry (spell_group 1016 keeps it from stacking with "
          "caster Faerie Fire). 6 sec cooldown (below 30 sec, no Cooldown Haste). spell_dru_thrash grants 1 Swell "
          "when it hits 3+ targets in Bestial Fury. Learned at 30. Visual: Swipe (Bear)'s. potency-system (PLAN P6 "
          "step 5 follow-up, 2026-10-01): both effects are ap-only (old coefficients 0/0.10 direct, 0/0.03 "
          "periodic, via the removed EffectBonusMultiplier_N overrides below) - ap_potency=40.7 (direct) and 6.7 "
          "(periodic) are druid-potency-report.md's base-implied defaults, matching the established P5/Feral "
          "convention; AP coefficients move 0.10 -> 0.175 (direct) and 0.03 -> 0.058 (periodic tick), base V60s "
          "essentially unchanged by construction. The third effect (armor reduction debuff) has no damage/heal "
          "component and is left untouched. Same structural follow-up as Pulverize/Savage Bite/Lacerate, just not "
          "named in the original pass's scope.",
    raw_overrides=_feral_new_raw(
        "Deals {pot1} damage to enemies within $a1 yards and causes them to bleed for {pot2.total} damage over $d.  "
        "Also reduces their armor by $s3% for $d.  While Bestial Fury is active, hitting 3 or more targets grants 1 "
        "stack of Swell.",
        "{pot2} damage every $t2 sec.  Armor reduced by $s3%.",
        **_BEAR_ATTACK_RAW, BaseLevel=30, SpellLevel=30, MaxLevel=80, SpellClassMask_3=THRASH,
        SpellVisualID_1=189,
    ),
)
trained_by(thrash_200423, trainer_id=216, req_level=30, money_cost=6000)
skill_line_ability(id=30437, skill_line=134, spell_id=thrash_200423.id, class_mask=1024)
scripted_by(thrash_200423, 'spell_dru_thrash')


bestial_fury_200425 = spell(
    id=200425,
    name='Bestial Fury',
    school=School.NORMAL,
    attributes=327696,  # Bear Form 5487's form attributes
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MOD_SHAPESHIFT, misc_value=ShapeshiftForm.BEAR),
        Effect(type=EffectType.APPLY_AURA, base_points=-66, implicit_target_a=1, apply_aura=AuraType.MOD_RESISTANCE_PCT, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=-71, implicit_target_a=1, apply_aura=AuraType.MOD_THREAT, misc_value=127),
    ],
    spell_icon_id=2229,
    notes="NEW (druid-rework FERAL §0.16 / CORE-AUDIT row 37, WP-BRIEF §3), talent 804: an alternate bear form - "
          "shifts into the stock FORM_BEAR (5) while the everyday bear is FORM_DIREBEAR (8); ShapeshiftMask 0x90 "
          "(forms 5 and 8) so the client does not flag it red while it is active (form 5); off the GCD, no cost, no "
          "cooldown; -65% armor, -70% threat; +50% rage from damage and Polymorph immunity ride on the hidden linked "
          "aura 200437 (linked_spell type 2, druid_talents.py). The "
          "3.5 sec swing is spellshapeshiftform_dbc form 5 (druid_talents.py). Clicking it again cancels the form; "
          "spell_dru_bestial_fury then recasts Bear Form 5487 keeping rage. spell_custom_attr POSITIVE (druid_talents.py) "
          "so the armor/threat penalties don't make it a debuff. No family bit. Form-spell layout and shift visual "
          "copied from Bear Form 5487; StanceBarOrder left 0 (same as Bear Form - the plan names no slot).",
    raw_overrides=_feral_new_raw(
        "Toggle.  Enter a Bestial Fury while in Bear Form, reducing your armor by $s2% and the threat you generate by "
        "$s3%.  Your attack speed becomes 3.5 sec, increasing the damage of each swing, and rage generated from damage "
        "dealt is increased by $200437s1%.  While active, Maul grants Swell, increasing your physical damage by "
        "$200426s1% per stack, stacking up to $200426u times.  Ironfur, Savage Defense and Survival Instincts cannot be "
        "used while active and are removed when it begins.  Leaving Bear Form ends Bestial Fury; toggling it off "
        "removes all Swell and returns you to Bear Form.",
        "Armor reduced by $s2%.  Threat generated reduced by $s3%.  Attack speed slowed to 3.5 sec.  Rage from damage "
        "dealt increased by $200437s1%.",
        AttributesEx=98304, AttributesEx4=2097152, ActiveIconID=122, RangeIndex=1, ShapeshiftMask=SS_ANY_BEAR,
        StartRecoveryCategory=0, StartRecoveryTime=0, SpellVisualID_1=653,
    ),
)
scripted_by(bestial_fury_200425, 'spell_dru_bestial_fury')


savage_bite_200439 = spell(
    id=200439,
    name='Savage Bite',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=93.06, potency_kind='direct', implicit_target_a=6),
    ],
    spell_icon_id=90122,  # spell_druid_bearhug, build_patch_i.py
    notes="NEW (docs/reworks/druid-feral-addition.md §2, FERAL-ADDENDUM §3.3): physical SCHOOL_DAMAGE, not a weapon "
          "attack, matching Pulverize's own real formula (SCHOOL_DAMAGE + AP, not the design doc's normalized-weapon-"
          "damage text) scaled by 250/150 - Pulverize's 59 + 5.0/level from 22 (+0.30 AP) x 5/3 = 98 + 8.333/level "
          "(+0.50 AP), ~581 at 80 vs Pulverize's ~349. Same BaseLevel/SpellLevel 22 as Pulverize (not the trainer "
          "level 10) so the ratio holds at every level >= 22; a level 10-21 druid with the Bestial Fury talent gets "
          "the flat level-22 value (SpellEffectInfo::CalcValue clamps level up to BaseLevel, SpellInfo.cpp:425-426), "
          "never a reduced or negative one. No cost, no cooldown, on the GCD. CasterAuraSpell 200438 (Tooth and "
          "Claw) is the server-enforced usability gate; the tooltip's own text covers the case where the client "
          "doesn't greyed-out the button for it. Shares Pulverize's family bit (PULVERIZE, FERAL-ADDENDUM §3.3 user "
          "decision) instead of a new one - reaches Nurturing Instinct's buff and Splintering Blows with no extra "
          "mask, not Pulverize's own id-keyed mechanics (Lacerate, Swell, Predatory Strikes/Primal Precision bear "
          "clauses). spell_dru_savage_bite consumes 1 Tooth and Claw charge and casts Nurturing Instinct's buff, "
          "same as a Predator's-Swiftness Regrowth. Icon 90122 (spell_druid_bearhug, mined by build_patch_i.py). "
          "Trainer-taught, not talent-granted (user override: simpler than a Bestial-Fury learner spell) - any druid "
          "can learn it, but it does nothing without the Bestial Fury talent. potency-system (PLAN P6 step 5, Feral "
          "pass): ap-only (old coefficient 0/0.50) - ap_potency=155.1 is druid-potency-report.md's base-implied "
          "default, matching the P5 convention (and still landing at almost exactly Pulverize's 93.5 x 5/3 = 155.8, "
          "preserving the intended ratio); AP coefficient moves 0.50 -> 0.665, base V60 415 -> ~415 (essentially "
          "unchanged by construction)."
          ' Effect 1 ap_potency 155.1 -> 124.08 (2026-10-08, DPS balance pass, user ruling: Bear DPS Savage Bite x0.80).'
          ' Effect 1 ap_potency 124.08 -> 93.06 (2026-10-08, DPS balance pass, user ruling: Bear DPS Savage Bite x0.75, round 9).',
    raw_overrides=_feral_new_raw(
        "Requires Tooth and Claw.  Deals {pot1} damage.  Consumes 1 charge of Tooth and "
        "Claw.",
        **_BEAR_ATTACK_RAW, BaseLevel=22, SpellLevel=22, MaxLevel=80, SpellClassMask_3=PULVERIZE,
        SpellVisualID_1=6586, DurationIndex=0, CasterAuraSpell=200438,
    ),
)
trained_by(savage_bite_200439, trainer_id=216, req_level=10, money_cost=600)
trained_by(savage_bite_200439, trainer_id=217, req_level=10, money_cost=600)
skill_line_ability(id=30439, skill_line=134, spell_id=savage_bite_200439.id, class_mask=1024)
scripted_by(savage_bite_200439, 'spell_dru_savage_bite')
