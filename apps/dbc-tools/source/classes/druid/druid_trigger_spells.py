"""
Druid - spells that are never directly cast - proc/periodic-tick effects, trigger_spell targets, hidden talent-rank buffs, etc..

Split from a single source/classes/druid.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .druid_...` below) resolve.
"""

from lib.dsl import RANGE_SELF, AuraType, CombatRating, DispelType, Effect, EffectType, Mechanic, PowerType, School, SpellModOp
from lib.dsl.constants import ShapeshiftForm
from lib.dsl.registry import bonus_coefficients, linked_spell, procs_on, scripted_by, skill_line_ability, spell
from ._masks import (
    BLOOM, CENARION_WARD, CENARION_WARD_HOT, CORE_HOT_CAST, CULTIVATION, DIRECT_NATURE_HEAL,
    DRUID_SPELL_DAMAGE, EMP_REJUV_COEFF, FORCE_OF_NATURE, FURY_OF_ELUNE, GENESIS_DOT, GENESIS_TICKS,
    HEALING_TOUCH, HEAL_DIRECT, HEAL_DOT, HURRICANE, INNERVATE, INSECT_SWARM, LIFEBLOOM,
    MASS_ENTANGLEMENT, MOONGLOW_SPELLS, NATURAL_ALACRITY, NATURES_REACH, PROC_ATTR_TRIGGERED_CAN_PROC,
    PROC_FLAG_DONE_MELEE_AUTO_ATTACK, PROC_FLAG_DONE_PERIODIC, PROC_FLAG_DONE_RANGED_AUTO_ATTACK,
    PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG, PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS,
    PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS, PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_NEG,
    PROC_FLAG_DONE_SPELL_RANGED_DMG_CLASS, PROC_FLAG_TAKEN_DAMAGE, PROC_HIT_CRITICAL,
    PROC_SPELL_PHASE_CAST, PROC_SPELL_PHASE_HIT, PROC_SPELL_TYPE_HEAL, REJUVENATION, REGROWTH,
    SHAPESHIFT_FORMS, STARFALL, STARFIRE, STARSURGE, SWIFTMEND, THORNS, TRANQUILITY, TYPHOON,
    WILD_GROWTH, WRATH, YSERAS_GIFT,
)
# druid-rework Feral pass (FERAL §4/§5/§7): Feral stock bits and composites.
from ._masks import (
    BEAR_FORM_PASSIVE, DEMORALIZING_ROAR, FERAL_BLEEDS, LACERATE, MAIM, MANGLE_BEAR, MANGLE_CAT, MAUL,
    NURTURING_INSTINCT_DAMAGE, NURTURING_INSTINCT_DOT, PROC_HIT_NORMAL, PROC_SPELL_TYPE_DAMAGE, PULVERIZE, RAKE,
    RAVAGE, RIP, RIP_FEROCIOUS_BITE, SAVAGE_ROAR, SHRED, SURVIVAL_INSTINCTS, SWIPE_BEAR, SWIPE_CAT, THRASH,
)

# druid-rework Feral pass: ShapeshiftMask/ShapeshiftExclude bits (`1 << (form - 1)`,
# SpellInfo::CheckShapeshift). Since FERAL §0.16 / CORE-AUDIT row 37 the everyday bear is FORM_DIREBEAR
# (8) at every level and Bestial Fury is the stock FORM_BEAR (5); "in bear" = either one.
SS_CAT = 1 << (ShapeshiftForm.CAT - 1)  # 0x01
SS_TREE = 1 << (ShapeshiftForm.TREE - 1)  # 0x02
SS_BESTIAL_FURY = 1 << (ShapeshiftForm.BEAR - 1)  # 0x10 - form 5, Bestial Fury only
SS_BEAR = 1 << (ShapeshiftForm.DIREBEAR - 1)  # 0x80 - form 8, the everyday bear (Bear Form 5487 / Dire Bear 9634)
SS_ANY_BEAR = SS_BESTIAL_FURY | SS_BEAR  # 0x90 = 144
SS_FERAL = SS_CAT | SS_ANY_BEAR  # 0x91 = 145


blood_frenzy_16952 = spell(
    id=16952,
    name='Blood Frenzy',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=16953),
    ],
    spell_icon_id=108,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx3': 524288, 'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your critical strikes from Cat Form abilities that add combo points  have a $h% chance to add an additional combo point.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'ShapeshiftMask': 1, 'SpellClassSet': 7},
)


hurricane_42231 = spell(
    id=42231,
    name='Hurricane',
    school=School.NATURE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=102.8, potency_kind='direct', implicit_target_a=76, implicit_target_b=16, radius_yards=8.0),
    ],
    spell_icon_id=220,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 40); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. Potency system P5 (druid pass): converted to sp_potency=102.8 (potency-report default, base/coef already agreed).',
    raw_overrides={'AttributesEx': 136, 'AttributesEx2': 1073741824, 'AttributesEx3': 1073741824, 'AttributesEx5': 1024, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 40, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Creates a violent storm in the target area causing {pot1} Nature damage to enemies every $16914t3 sec, and increasing the time between attacks of enemies by $16914s2%.  Lasts $16914d.  Druid must channel to maintain the spell.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 135, 'SpellClassMask_1': 4194304, 'SpellClassSet': 7, 'SpellLevel': 40, 'SpellPriority': 50, 'SpellVisualID_1': 9491, 'StartRecoveryCategory': 133},
)


tranquility_44203 = spell(
    id=44203,
    name='Tranquility',
    school=School.NATURE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.HEAL, sp_potency=185.1, potency_kind='heal', implicit_target_a=76, implicit_target_b=34, radius_yards=30.0),
    ],
    spell_icon_id=220,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 30); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 7 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. Potency system P5 (druid pass): converted to sp_potency=185.1 (potency-report default, base/coef already agreed).',
    raw_overrides={'AttributesEx2': 1610612740, 'AttributesEx3': 1073742336, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals all nearby group members for {pot1} every $740t2 seconds for $740d.  Druid must channel to maintain the spell.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 135, 'SpellClassMask_1': 128, 'SpellClassSet': 7, 'SpellLevel': 30, 'SpellPriority': 50, 'StartRecoveryCategory': 133},
)


natural_perfection_45281 = spell(
    id=45281,
    name='Natural Perfection',
    school=School.NORMAL,
    dispel=DispelType.MAGIC,
    attributes=150994944,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-3, points_per_level=-0.03333333333333333, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
    ],
    spell_icon_id=2250,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx4': 128, 'AttributesEx5': 8, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Reduces all damage taken by $s1%.', 'CastingTimeIndex': 1, 'CumulativeAura': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your critical strike chance with all spells is increased by $33881s2% and critical strikes against you give you the Natural Perfection effect reducing all damage taken by $45281s1%.  Stacks up to $45281u times.  Lasts $45281d.', 'EffectBasePoints_2': -1, 'EffectBasePoints_3': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 32, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 2097152, 'SpellClassSet': 7, 'SpellVisualID_1': 10115},
)


nurturing_instinct_47179 = spell(
    id=47179,
    name='Nurturing Instinct',
    school=School.NORMAL,
    attributes=400,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, points_per_level=0.16666666666666666, implicit_target_a=1, apply_aura=AuraType.MOD_HEALING_PCT, misc_value=127),
    ],
    spell_icon_id=2254,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your healing spells by up to $s1% of your Agility, and increases healing done to you by $47179s1% while in Cat form.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 33554432, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 1, 'SpellClassSet': 7},
)


spark_of_nature_48435 = spell(
    id=48435,
    name='Spark of Nature',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, points_per_level=0.16666666666666666, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=337,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical effect chance of your Swiftmend and Nourish spells by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 33554434, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


improved_moonkin_form_50170 = spell(
    id=50170,
    name='Improved Moonkin Form',
    school=School.NATURE,
    attributes=400,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=65, points_per_level=0.03333333333333333, implicit_target_a=1, apply_aura=193, radius_yards=100.0),
    ],
    spell_icon_id=2855,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 268436480, 'AttributesEx4': 2097152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712188, 'EffectBasePoints_2': -1, 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_2': 8192, 'EffectSpellClassMaskB_1': 1024, 'EffectSpellClassMaskC_2': 8192, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 1073741824, 'SpellClassSet': 7, 'SpellVisualID_1': 13458},
)


starfall_50286 = spell(
    id=50286,
    name='Starfall',
    school=School.ARCANE | School.NATURE,  # Astral (druid-rework BALANCE §6 row 8,1)
    attributes=384,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=50287, implicit_target_a=22, implicit_target_b=15, radius_yards=30.0),
    ],
    spell_icon_id=122,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 60); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 4 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 525448, 'AttributesEx3': 196608, 'AttributesEx4': 128, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'You summon a flurry of stars from the sky on all targets within 30 yards of the caster, each dealing $50288s1 Arcane damage. Also causes $50294s1 Arcane damage to all other enemies within $50294a1 yards of the enemy target. Maximum 20 stars. Lasts $48505d.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You summon a flurry of stars from the sky on all targets within $50286a yards of the caster, each dealing $50288s1 Arcane damage. Also causes $50294s1 Arcane damage to all other enemies within $50294a1 yards of the enemy target. Maximum 20 stars. Lasts $48505d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_3': 256, 'SpellClassSet': 7, 'SpellLevel': 60, 'StartRecoveryTime': 1500},
)


starfall_50288 = spell(
    id=50288,
    name='Starfall',
    school=School.ARCANE | School.NATURE,  # Astral (druid-rework BALANCE §6 row 8,1)
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=58.3, potency_kind='direct', implicit_target_a=6),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=6, trigger_spell=50294),
    ],
    spell_icon_id=2854,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 60); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 4 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. Potency system P5 (druid pass): converted to sp_potency=58.3 (potency-report default, base/coef already agreed).',
    raw_overrides={'AttributesEx': 128, 'AttributesEx2': 1073741828, 'AttributesEx3': 1049089, 'AttributesEx4': 128, 'AttributesEx5': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'You summon a flurry of stars from the sky on all targets within 30 yards of the caster, each dealing {pot1} Arcane damage. Also causes $50294s1 Arcane damage to all other enemies within $50294a1 yards of the enemy target. Maximum 20 stars. Lasts $48505d.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You summon a flurry of stars from the sky on all targets within 30 yards of the caster, each dealing {pot1} Arcane damage. Also causes $50294s1 Arcane damage to all other enemies within $50294a1 yards of the enemy target. Maximum 20 stars. Lasts $48505d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassMask_2': 8388608, 'SpellClassSet': 7, 'SpellLevel': 60, 'SpellVisualID_1': 11040},
)


starfall_50294 = spell(
    id=50294,
    name='Starfall',
    school=School.ARCANE | School.NATURE,  # Astral (druid-rework BALANCE §6 row 8,1)
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=9.7, potency_kind='direct', implicit_target_a=53, implicit_target_b=16, radius_yards=5.0),
    ],
    spell_icon_id=2854,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 60); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 4 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. Potency system P5 (druid pass): converted to sp_potency=9.7 (potency-report default, base/coef already agreed).',
    raw_overrides={'AttributesEx': 136, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'You summon a flurry of stars from the sky on all targets within 30 yards of the caster, each dealing $50288s1 Arcane damage. Also causes {pot1} Arcane damage to all other enemies within $50294a1 yards of the enemy target. Maximum 20 stars. Lasts $48505d.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You summon a flurry of stars from the sky on all targets within 30 yards of the caster, each dealing $50288s1 Arcane damage. Also causes {pot1} Arcane damage to all other enemies within $50294a1 yards of the enemy target. Maximum 20 stars. Lasts $48505d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 8388608, 'SpellClassSet': 7, 'SpellLevel': 60, 'StartRecoveryCategory': 133},
)


infected_wounds_58179 = spell(
    id=58179,
    name='Infected Wounds',
    school=School.NATURE,
    dispel=DispelType.DISEASE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=12000,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=-8, mechanic=8, implicit_target_a=6, apply_aura=AuraType.MOD_MELEE_HASTE),
    ],
    spell_icon_id=2857,
    notes="druid-rework FERAL §7 (7,3): Infected Wounds' Mangle slow - eff0 movement snare removed, eff1 attack speed -7/-14/-20% flat (ppl 0); cast by spell_dru_mangle for the caster's rank.",
    raw_overrides={'AttributesEx': 131208, 'AttributesEx2': 16777216, 'AttributesEx3': 131072, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Attack speed slowed by $s2%.', 'BaseLevel': 50, 'CastingTimeIndex': 1, 'CumulativeAura': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your Mangle reduces the target's attack speed by $58179s2% for $58179d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712172, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassSet': 7, 'SpellLevel': 50, 'SpellVisualID_1': 11569},
)


earth_and_moon_60431 = spell(
    id=60431,
    name='Earth and Moon',
    school=School.ARCANE,
    dispel=DispelType.MAGIC,
    attributes=8388608,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, points_per_level=0.0, implicit_target_a=6, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
    ],
    spell_icon_id=2991,
    notes='pulled from existing data; druid-rework BALANCE §6 row (9,1): duration 12s->8s; eff1 base_points is now overridden by the proc\'s BP0 (aura 42->231 on 48506/48510/48511), so its own stored value is a display-only fallback; stays in spell group 1101 (EXCLUSIVE_SAME_EFFECT with Curse of the Elements/Ebon Plaguebringer)',
    raw_overrides={'AttributesEx': 136, 'AttributesEx2': 4, 'AttributesEx3': 131072, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Magic damage taken increased by $s1%.', 'CastingTimeIndex': 1, 'CumulativeAura': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Wrath, Starfire, and Starsurge apply the Earth and Moon effect, which increases magic damage taken by $s1% for $d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712172, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassSet': 7},
)


typhoon_61391 = spell(
    id=61391,
    name='Typhoon',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.KNOCK_BACK, base_points=69, implicit_target_a=104, misc_value=150, radius_yards=30.0),
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=291.6, potency_kind='direct', implicit_target_a=104, radius_yards=30.0),
        Effect(type=EffectType.APPLY_AURA, base_points=-51, mechanic=Mechanic.SNARE, implicit_target_a=104, apply_aura=AuraType.MOD_DECREASE_SPEED, radius_yards=30.0),
    ],
    spell_icon_id=15,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 50); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80; druid-rework BALANCE §4: BaseLevel/SpellLevel 50->36, eff2 retuned to match 50516. Potency system P5 (druid pass): converted to sp_potency=291.6 (potency-report default, base/coef already agreed).',
    raw_overrides={'AttributesEx': 128, 'AttributesEx2': 524288, 'AttributesEx3': 512, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Dazed.', 'BaseLevel': 36, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You summon a violent Typhoon that does {pot2} Nature damage when in contact with hostile targets, knocking them back and dazing them for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'ShapeshiftExclude': 2, 'ShapeshiftMask': 1073741824, 'Speed': 30.0, 'SpellClassMask_2': 16777216, 'SpellClassSet': 7, 'SpellLevel': 36, 'SpellVisualID_1': 10437},
)


owlkin_frenzy_48389 = spell(
    id=48389,
    name='Owlkin Frenzy',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL_WITH_VALUE, trigger_spell=48391),
    ],
    spell_icon_id=2853,
    notes='pulled from existing data | moved here from source/classes/mage.py (spell-source-dsl.PLAN.md - a split_class_file.py spot check turned up this and its two sibling ranks misfiled into Mage). druid-rework BALANCE §6 row (7,0): aura 42->231, SpellClassSet 3->7 (fixes the misfiled-as-Mage bug), classmask cleared; procs_on(-48389, ...) in druid_talents.py drives the real proc logic',
    raw_overrides={'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While in Moonkin Form, your direct Arcane and Nature damage spells have a 10% chance to trigger Owlkin Frenzy, and melee hits against you have a 30% chance. Owlkin Frenzy increases your Arcane and Nature damage by $48391s1% for $48391d, and restores $48391s3% of base mana every $48391t3 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'ProcTypeMask': 0, 'RangeIndex': 1, 'ShapeshiftMask': 1073741824, 'SpellClassSet': 7, 'SpellLevel': 1, 'SpellPriority': 50},
)


owlkin_frenzy_48392 = spell(
    id=48392,
    name='Owlkin Frenzy',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL_WITH_VALUE, trigger_spell=48391),
    ],
    spell_icon_id=2853,
    notes='pulled from existing data | moved here from source/classes/mage.py - see owlkin_frenzy_48389\'s notes. druid-rework BALANCE §6 row (7,0)',
    raw_overrides={'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While in Moonkin Form, your direct Arcane and Nature damage spells have a 10% chance to trigger Owlkin Frenzy, and melee hits against you have a 30% chance. Owlkin Frenzy increases your Arcane and Nature damage by $48391s1% for $48391d, and restores $48391s3% of base mana every $48391t3 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'ProcTypeMask': 0, 'RangeIndex': 1, 'ShapeshiftMask': 1073741824, 'SpellClassSet': 7, 'SpellLevel': 1, 'SpellPriority': 50},
)


owlkin_frenzy_48393 = spell(
    id=48393,
    name='Owlkin Frenzy',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL_WITH_VALUE, trigger_spell=48391),
    ],
    spell_icon_id=2853,
    notes='pulled from existing data | moved here from source/classes/mage.py - see owlkin_frenzy_48389\'s notes. druid-rework BALANCE §6 row (7,0)',
    raw_overrides={'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While in Moonkin Form, your direct Arcane and Nature damage spells have a 10% chance to trigger Owlkin Frenzy, and melee hits against you have a 30% chance. Owlkin Frenzy increases your Arcane and Nature damage by $48391s1% for $48391d, and restores $48391s3% of base mana every $48391t3 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'ProcTypeMask': 0, 'RangeIndex': 1, 'ShapeshiftMask': 1073741824, 'SpellClassSet': 7, 'SpellLevel': 1, 'SpellPriority': 50},
)


starlight_wrath_16814 = spell(
    id=16814,
    name='Starlight Wrath',
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
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CRITICAL_CHANCE),
    ],
    spell_icon_id=263,
    notes='pulled from existing data; druid-rework BALANCE §6 row (0,1): cast-time-reduction SpellMod replaced with a Wrath damage % + Starfire/Starsurge crit % (base cast times drop instead - §0.13)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Wrath by $s1%. Increases the critical strike chance of your Starfire and Starsurge by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': WRATH, 'EffectSpellClassMaskB_1': STARFIRE, 'EffectSpellClassMaskB_3': STARSURGE, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


starlight_wrath_16815 = spell(
    id=16815,
    name='Starlight Wrath',
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
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CRITICAL_CHANCE),
    ],
    spell_icon_id=263,
    notes='pulled from existing data; druid-rework BALANCE §6 row (0,1)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Wrath by $s1%. Increases the critical strike chance of your Starfire and Starsurge by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': WRATH, 'EffectSpellClassMaskB_1': STARFIRE, 'EffectSpellClassMaskB_3': STARSURGE, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


starlight_wrath_16816 = spell(
    id=16816,
    name='Starlight Wrath',
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
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CRITICAL_CHANCE),
    ],
    spell_icon_id=263,
    notes='pulled from existing data; druid-rework BALANCE §6 row (0,1)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Wrath by $s1%. Increases the critical strike chance of your Starfire and Starsurge by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': WRATH, 'EffectSpellClassMaskB_1': STARFIRE, 'EffectSpellClassMaskB_3': STARSURGE, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


starlight_wrath_16817 = spell(
    id=16817,
    name='Starlight Wrath',
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
    spell_icon_id=263,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cast time of your Wrath and Starfire spells by $/1000;S1 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 5, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


starlight_wrath_16818 = spell(
    id=16818,
    name='Starlight Wrath',
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
    spell_icon_id=263,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cast time of your Wrath and Starfire spells by $/1000;S1 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 5, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


nature_s_reach_16819 = spell(
    id=16819,
    name="Nature's Reach",
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
    ],
    spell_icon_id=39,
    notes='pulled from existing data; druid-rework BALANCE §6 row (2,3): range-% SpellMod replaced with a flat +yd RANGE SpellMod re-scoped to NATURES_REACH (Wrath/Starfire/Entangling Roots/Hurricane/Cyclone/Mass Entanglement); threat and Faerie Fire (Feral) range effects dropped',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of your damaging spells with a channeling or cast time by $m1 yards, and the range of your Entangling Roots, Mass Entanglement, and Cyclone by $m1 yards. Does not stack with similar effects.\n\n|cFF9D9D9DCapstone Bonus: When your Arcane spells with a cast time hit a target afflicted by your Moonfire, it spreads to all unafflicted enemies within 5 yards. This effect has a 6 sec cooldown.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': NATURES_REACH[0], 'EffectSpellClassMaskA_2': NATURES_REACH[1], 'EffectSpellClassMaskA_3': NATURES_REACH[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


nature_s_reach_16820 = spell(
    id=16820,
    name="Nature's Reach",
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
    ],
    spell_icon_id=39,
    notes='pulled from existing data; druid-rework BALANCE §6 row (2,3): final rank, carries the Moonfire-spread capstone (procs_on(16820, ...) in druid_talents.py, spell_dru_natures_reach_moonfire_spread)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of your damaging spells with a channeling or cast time by $m1 yards, and the range of your Entangling Roots, Mass Entanglement, and Cyclone by $m1 yards. Does not stack with similar effects.\n\nCapstone Bonus: When your Arcane spells with a cast time hit a target afflicted by your Moonfire, it spreads to all unafflicted enemies within 5 yards. This effect has a 6 sec cooldown.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': NATURES_REACH[0], 'EffectSpellClassMaskA_2': NATURES_REACH[1], 'EffectSpellClassMaskA_3': NATURES_REACH[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


improved_moonfire_16821 = spell(
    id=16821,
    name='Improved Moonfire',
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
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=71, misc_value=64),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=225,
    notes='pulled from existing data; druid-rework BALANCE §6 row (1,2): eff1 moved from a Moonfire-scoped crit SpellMod to MOD_SPELL_CRIT_CHANCE_SCHOOL(71)/Arcane (feeds Astral via CORE-AUDIT row 5\'s linked_spell 200354-200356)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Moonfire by $s2% and the critical strike chance of your Arcane spells by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Your direct Arcane critical strikes on targets afflicted by your Moonfire trigger an extra $200341s1 Arcane damage. This can occur once every 1.5 sec.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 2, 'EffectSpellClassMaskC_1': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


improved_moonfire_16822 = spell(
    id=16822,
    name='Improved Moonfire',
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
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=71, misc_value=64),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=225,
    notes='pulled from existing data; druid-rework BALANCE §6 row (1,2)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Moonfire by $s2% and the critical strike chance of your Arcane spells by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Your direct Arcane critical strikes on targets afflicted by your Moonfire trigger an extra $200341s1 Arcane damage. This can occur once every 1.5 sec.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 2, 'EffectSpellClassMaskC_1': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


natural_shapeshifter_16833 = spell(
    id=16833,
    name='Natural Shapeshifter',
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
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=122,
    notes="druid-rework RESTO §8 (0,2), moved from (1,2): replaces the stock shapeshift-cost-reduction effects with two APPLY_AURA+DUMMY markers Druid::ApplyShapeshiftFormBonuses reads (CORE-AUDIT row 16) - eff1 is the 2/4/6% bucket (bear physical dmg, moonkin Arcane+Nature dmg), eff2 is the 1/2/3% bucket (cat crit, no-form/Tree of Life healing). 200573 (druid_trigger_spells.py) is the no-form healing buff it casts. scripted_by: spell_dru_natural_shapeshifter (AuraScript, Apply/Remove REAL) re-evaluates on learn/login/unlearn. Code-review fix: both markers were plain SPELL_EFFECT_DUMMY, so the talent had zero aura effects and neither the C++ reads nor the AuraScript's Apply/Remove hooks ever fired.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Bear Form: physical damage increased by $s1%. Cat Form: melee critical strike chance increased by $s2%. Moonkin Form: Arcane and Nature damage increased by $s1%. No form or Tree of Life: healing increased by $s2%.\n\n|cFF9D9D9DCapstone Bonus: Reduces the global cooldown of your shapeshifts to 1 sec.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


natural_shapeshifter_16834 = spell(
    id=16834,
    name='Natural Shapeshifter',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=122,
    notes='druid-rework RESTO §8 (0,2): rank 2 of the DUMMY-marker rewrite above.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Bear Form: physical damage increased by $s1%. Cat Form: melee critical strike chance increased by $s2%. Moonkin Form: Arcane and Nature damage increased by $s1%. No form or Tree of Life: healing increased by $s2%.\n\n|cFF9D9D9DCapstone Bonus: Reduces the global cooldown of your shapeshifts to 1 sec.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


natural_shapeshifter_16835 = spell(
    id=16835,
    name='Natural Shapeshifter',
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
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-501, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.GLOBAL_COOLDOWN),
    ],
    spell_icon_id=122,
    notes="druid-rework RESTO §8 (0,2): rank 3, the capstone rank - duration_ms 6000->-1 (permanent while learned, matching the other capstone-carrying ranks); new eff3 flat GLOBAL_COOLDOWN -500 ms scoped to SHAPESHIFT_FORMS (C_1/C_2) - shapeshift GCD drops to 1 sec (clamped to 1000 ms floor, Spell.cpp:9256).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Bear Form: physical damage increased by $s1%. Cat Form: melee critical strike chance increased by $s2%. Moonkin Form: Arcane and Nature damage increased by $s1%. No form or Tree of Life: healing increased by $s2%.\n\nCapstone Bonus: Reduces the global cooldown of your shapeshifts to 1 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskC_1': SHAPESHIFT_FORMS[0], 'EffectSpellClassMaskC_2': SHAPESHIFT_FORMS[1], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)
scripted_by(natural_shapeshifter_16833, 'spell_dru_natural_shapeshifter')
scripted_by(natural_shapeshifter_16834, 'spell_dru_natural_shapeshifter')
scripted_by(natural_shapeshifter_16835, 'spell_dru_natural_shapeshifter')


brambles_16836 = spell(
    id=16836,
    name='Brambles',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-10001, implicit_target_a=1, apply_aura=107, misc_value=SpellModOp.COOLDOWN),
    ],
    spell_icon_id=53,
    notes='pulled from existing data; druid-rework BALANCE §6 row (4,3): eff1 stays an APPLY_AURA+DUMMY storing the Thorns % (CORE-AUDIT row 2: Unit.cpp\'s stock Brambles clause reads it via GetAuraEffectOfRankedSpell(16836, 0); a Thorns DAMAGE SpellMod here also applied on top of that clause, once at shield calc and again at proc, so Thorns took x8/x27/x64 instead of x2/x3/x4 - code-review fix); eff2 becomes a plain DUMMY (Druid::AddSwell/treant script reads EFFECT_1 directly); eff3 repurposed off Barkskin\'s CHANCE_OF_SUCCESS hack (CORE-AUDIT row 2) onto a Force of Nature cooldown SpellMod',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Thorns by $s1% and the damage done by your Treants by $s2%. Reduces the cooldown of Force of Nature by $/1000;s3 sec.\n\n|cFF9D9D9DCapstone Bonus: Your Entangling Roots also silence the target for 4 sec. This effect has a 10 sec cooldown.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': THORNS, 'EffectSpellClassMaskC_2': FORCE_OF_NATURE, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


brambles_16839 = spell(
    id=16839,
    name='Brambles',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=199, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-20001, implicit_target_a=1, apply_aura=107, misc_value=SpellModOp.COOLDOWN),
    ],
    spell_icon_id=53,
    notes='pulled from existing data; druid-rework BALANCE §6 row (4,3): junk misc 28 on eff1 cleared (eff1 stays DUMMY, see 16836)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Thorns by $s1% and the damage done by your Treants by $s2%. Reduces the cooldown of Force of Nature by $/1000;s3 sec.\n\n|cFF9D9D9DCapstone Bonus: Your Entangling Roots also silence the target for 4 sec. This effect has a 10 sec cooldown.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': THORNS, 'EffectSpellClassMaskC_2': FORCE_OF_NATURE, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


brambles_16840 = spell(
    id=16840,
    name='Brambles',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=299, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=59, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-30001, implicit_target_a=1, apply_aura=107, misc_value=SpellModOp.COOLDOWN),
    ],
    spell_icon_id=53,
    notes='pulled from existing data; druid-rework BALANCE §6 row (4,3): final rank, carries the Entangling Roots silence capstone (procs_on(16840, ...) in druid_talents.py, spell_dru_brambles_silence, WP-B; new debuff 200353)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Thorns by $s1% and the damage done by your Treants by $s2%. Reduces the cooldown of Force of Nature by $/1000;s3 sec.\n\nCapstone Bonus: Your Entangling Roots also silence the target for 4 sec. This effect has a 10 sec cooldown.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': THORNS, 'EffectSpellClassMaskC_2': FORCE_OF_NATURE, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


moonglow_16845 = spell(
    id=16845,
    name='Moonglow',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-4, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COST),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200348),
    ],
    spell_icon_id=310,
    notes='pulled from existing data; druid-rework BALANCE §6 row (1,0): cost re-scoped to MOONGLOW_SPELLS (Wrath/Starfire/Healing Touch/Regrowth/Swiftmend/Starsurge), new eff2 procs a stacking Spirit+regen buff (200348-200350, procs_on(-16845, ...) in druid_talents.py)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your Starfire, Wrath, Starsurge, Healing Touch, Regrowth, and Swiftmend by $s1%. Casting these spells has a 5% chance to increase your Spirit and your mana regeneration while casting. Does not stack with similar effects.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': MOONGLOW_SPELLS[0], 'EffectSpellClassMaskA_2': MOONGLOW_SPELLS[1], 'EffectSpellClassMaskA_3': MOONGLOW_SPELLS[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


moonglow_16846 = spell(
    id=16846,
    name='Moonglow',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-7, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COST),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200349),
    ],
    spell_icon_id=310,
    notes='pulled from existing data; druid-rework BALANCE §6 row (1,0)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your Starfire, Wrath, Starsurge, Healing Touch, Regrowth, and Swiftmend by $s1%. Casting these spells has a 5% chance to increase your Spirit and your mana regeneration while casting. Does not stack with similar effects.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': MOONGLOW_SPELLS[0], 'EffectSpellClassMaskA_2': MOONGLOW_SPELLS[1], 'EffectSpellClassMaskA_3': MOONGLOW_SPELLS[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


moonglow_16847 = spell(
    id=16847,
    name='Moonglow',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-10, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COST),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200350),
    ],
    spell_icon_id=310,
    notes='pulled from existing data; druid-rework BALANCE §6 row (1,0)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your Starfire, Wrath, Starsurge, Healing Touch, Regrowth, and Swiftmend by $s1%. Casting these spells has a 5% chance to increase your Spirit and your mana regeneration while casting. Does not stack with similar effects.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': MOONGLOW_SPELLS[0], 'EffectSpellClassMaskA_2': MOONGLOW_SPELLS[1], 'EffectSpellClassMaskA_3': MOONGLOW_SPELLS[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


celestial_focus_16850 = spell(
    id=16850,
    name='Celestial Focus',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=AuraType.REDUCE_PUSHBACK),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL, misc_value=0),
    ],
    spell_icon_id=1485,
    notes='pulled from existing data; druid-rework BALANCE §6 row (3,2): trimmed 3->2 ranks; REDUCE_PUSHBACK(149) applies to every spell so the classmask is cleared',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell, ranged, and melee haste by $s2%. Reduces the pushback suffered from damaging attacks by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Your Moonfire and Insect Swarm periodic damage has a chance to grant Shooting Stars, empowering your next Starsurge within 15 sec to not trigger its cooldown and be a guaranteed critical strike.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'ProcTypeMask': 0, 'RangeIndex': 1, 'SpellClassSet': 7},
)


feral_aggression_16858 = spell(
    id=16858,
    name='Feral Aggression',
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
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=960,
    notes='druid-rework FERAL §7 (1,3), moved from (0,2), trimmed 5->3 ranks (16861/16862 orphaned): rank 1/3 - eff0 APPLY_AURA DUMMY 5/10/15% damage vs targets above 75% health (Druid damage hooks), eff1 APPLY_AURA DUMMY 2/4/6% AP in forms (form-boost BP1 of 24899/24900). No ShapeshiftMask (WP-BRIEF §3).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage you do to targets above 75% health by $s1%. Increases your attack power in Cat, Bear and Dire Bear Form by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


feral_aggression_16859 = spell(
    id=16859,
    name='Feral Aggression',
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
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=960,
    notes='druid-rework FERAL §7 (1,3), moved from (0,2), trimmed 5->3 ranks (16861/16862 orphaned): rank 2/3 - eff0 APPLY_AURA DUMMY 5/10/15% damage vs targets above 75% health (Druid damage hooks), eff1 APPLY_AURA DUMMY 2/4/6% AP in forms (form-boost BP1 of 24899/24900). No ShapeshiftMask (WP-BRIEF §3).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage you do to targets above 75% health by $s1%. Increases your attack power in Cat, Bear and Dire Bear Form by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


feral_aggression_16860 = spell(
    id=16860,
    name='Feral Aggression',
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
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=960,
    notes='druid-rework FERAL §7 (1,3), moved from (0,2), trimmed 5->3 ranks (16861/16862 orphaned): rank 3/3 - eff0 APPLY_AURA DUMMY 5/10/15% damage vs targets above 75% health (Druid damage hooks), eff1 APPLY_AURA DUMMY 2/4/6% AP in forms (form-boost BP1 of 24899/24900). No ShapeshiftMask (WP-BRIEF §3).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage you do to targets above 75% health by $s1%. Increases your attack power in Cat, Bear and Dire Bear Form by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


feral_aggression_16861 = spell(
    id=16861,
    name='Feral Aggression',
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
        Effect(type=EffectType.APPLY_AURA, base_points=31, implicit_target_a=1, apply_aura=108, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=960,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the attack power reduction of your Demoralizing Roar by $s1% and the damage caused by your Ferocious Bite by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectItemType_1': 8, 'EffectItemType_2': 8388608, 'EffectSpellClassMaskA_1': 8, 'EffectSpellClassMaskB_1': 8388608, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


feral_aggression_16862 = spell(
    id=16862,
    name='Feral Aggression',
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
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=108, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=960,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the attack power reduction of your Demoralizing Roar by $s1% and the damage caused by your Ferocious Bite by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectItemType_1': 8, 'EffectItemType_2': 8388608, 'EffectSpellClassMaskA_1': 8, 'EffectSpellClassMaskB_1': 8388608, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


omen_of_clarity_16864 = spell(
    id=16864,
    name='Omen of Clarity',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=16870),
    ],
    spell_icon_id=1754,
    notes="druid-rework RESTO §8 (2,1): rank 1 of 3 (grown from a single stock rank); ProcTypeMask zeroed - proc conditions now come entirely from procs_on() below plus the rewritten spell_dru_omen_of_clarity_resto::CheckProc (direct Nature heals, direct damage, and Lifebloom's periodic heal only). Corrections item 1: the stock binding is displaced to a new class (unbind_script/scripted_by below).",
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Each damage and healing spell and auto attacks have a chance of causing the caster to enter a Clearcasting state.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your direct damage including auto attacks, your direct Nature healing spells, and the periodic healing of your Lifebloom have a $s1% chance to trigger Clearcasting, reducing the Mana, Rage or Energy cost of your next damaging or healing spell or offensive ability by 100%. 2 sec internal cooldown.\n\n|cFF9D9D9DCapstone Bonus: The spell or ability that consumes Clearcasting deals 10% increased damage and healing.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 26, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ProcTypeMask': 0, 'RangeIndex': 1, 'SpellClassMask_2': 2097152, 'SpellClassSet': 7, 'SpellLevel': 20, 'SpellVisualID_1': 4040, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


omen_of_clarity_200600 = spell(
    id=200600,
    name='Omen of Clarity',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=16870),
    ],
    spell_icon_id=1754,
    notes='druid-rework RESTO §8 (2,1): rank 2 - a clone of 16864 (same trigger, 16870), higher proc chance (procs_on below).',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Each damage and healing spell and auto attacks have a chance of causing the caster to enter a Clearcasting state.', 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your direct damage including auto attacks, your direct Nature healing spells, and the periodic healing of your Lifebloom have a $s1% chance to trigger Clearcasting, reducing the Mana, Rage or Energy cost of your next damaging or healing spell or offensive ability by 100%. 2 sec internal cooldown.\n\n|cFF9D9D9DCapstone Bonus: The spell or ability that consumes Clearcasting deals 10% increased damage and healing.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ProcTypeMask': 0, 'RangeIndex': 1, 'SpellClassMask_2': 2097152, 'SpellClassSet': 7, 'SpellVisualID_1': 4040, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


omen_of_clarity_200601 = spell(
    id=200601,
    name='Omen of Clarity',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200572),
    ],
    spell_icon_id=1754,
    notes='druid-rework RESTO §8 (2,1): rank 3, the final/capstone rank - triggers 200572 (the Clearcasting variant that also carries the +10% capstone bonus) instead of 16870.',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Each damage and healing spell and auto attacks have a chance of causing the caster to enter a Clearcasting state.', 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your direct damage including auto attacks, your direct Nature healing spells, and the periodic healing of your Lifebloom have a $s1% chance to trigger Clearcasting, reducing the Mana, Rage or Energy cost of your next damaging or healing spell or offensive ability by 100%. 2 sec internal cooldown.\n\nCapstone Bonus: The spell or ability that consumes Clearcasting deals 10% increased damage and healing.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ProcTypeMask': 0, 'RangeIndex': 1, 'SpellClassMask_2': 2097152, 'SpellClassSet': 7, 'SpellVisualID_1': 4040, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


nature_s_grace_16880 = spell(
    id=16880,
    name="Nature's Grace",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL_WITH_VALUE, trigger_spell=16886),
    ],
    spell_icon_id=10,
    notes='pulled from existing data; druid-rework BALANCE §6 row (2,0): aura 42->231 (value overrides 16886\'s own amount); procs_on(-16880, ...) in druid_talents.py overrides the stock -16880 row',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your direct damage and healing Druid spell critical strikes have a $h% chance to grant Nature\'s Grace, increasing spell, ranged, and melee haste by $16886s1% for $16886d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 33, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 7},
)


moonfury_16896 = spell(
    id=16896,
    name='Moonfury',
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
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=46,
    notes='pulled from existing data; druid-rework BALANCE §6 row (5,1): +Starsurge to eff1\'s mask; new eff3 scopes a separate Starfall damage %',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Starfire, Moonfire, Wrath, and Starsurge by $s1%, and your Starfall damage by $s3%.\n\n|cFF9D9D9DCapstone Bonus: Casting Starsurge grants Astral Surge, increasing your spell power for Arcane and Nature damage by 10% for 15 sec. Stacks up to 3 times; each stack has its own duration and multiplies the others.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 7, 'EffectSpellClassMaskA_3': STARSURGE, 'EffectSpellClassMaskB_1': 2, 'EffectSpellClassMaskC_2': STARFALL, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


moonfury_16897 = spell(
    id=16897,
    name='Moonfury',
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
        Effect(type=EffectType.APPLY_AURA, base_points=13, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=46,
    notes='pulled from existing data; druid-rework BALANCE §6 row (5,1)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Starfire, Moonfire, Wrath, and Starsurge by $s1%, and your Starfall damage by $s3%.\n\n|cFF9D9D9DCapstone Bonus: Casting Starsurge grants Astral Surge, increasing your spell power for Arcane and Nature damage by 10% for 15 sec. Stacks up to 3 times; each stack has its own duration and multiplies the others.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 7, 'EffectSpellClassMaskA_3': STARSURGE, 'EffectSpellClassMaskB_1': 2, 'EffectSpellClassMaskC_2': STARFALL, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


moonfury_16899 = spell(
    id=16899,
    name='Moonfury',
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
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=46,
    notes='pulled from existing data; druid-rework BALANCE §6 row (5,1): final rank, carries the Astral Surge capstone (spell_dru_starsurge AfterCast checks HasAura(16899) -> Druid::ApplyAstralSurge, WP-B)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Starfire, Moonfire, Wrath, and Starsurge by $s1%, and your Starfall damage by $s3%.\n\nCapstone Bonus: Casting Starsurge grants Astral Surge, increasing your spell power for Arcane and Nature damage by 10% for 15 sec. Stacks up to 3 times; each stack has its own duration and multiplies the others.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 7, 'EffectSpellClassMaskA_3': STARSURGE, 'EffectSpellClassMaskB_1': 2, 'EffectSpellClassMaskC_2': STARFALL, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


vengeance_16909 = spell(
    id=16909,
    name='Vengeance',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=47,
    notes='pulled from existing data; druid-rework BALANCE §6 row (6,3): trimmed 5->3 ranks, mask widened to DRUID_SPELL_DAMAGE (every druid magic-damage spell). warlock-rework AFFLICTION §4.8 (A1/A2, server-wide): crit-damage SpellMod zeroed, mask cleared; linked to hidden passive 200695 (165%). Note: aura 163 (MOD_CRIT_DAMAGE_BONUS) reads only the caster, so this no longer reaches pet/guardian spells the old SpellMod-108 reached via GetSpellModOwner (accepted, A1).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spell critical strikes now deal 165% damage. This does not stack with other similar effects.\n\n|cFF9D9D9DCapstone Bonus: Your direct Arcane and Nature critical strikes have a 15% chance to attract a Vengeful Soul, increasing your magic damage by 8% for 12 sec. When it ends, the Soul leaves your body and restores 10% of your missing mana. Only one Vengeful Soul can be attracted at a time, and a new proc refreshes it.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)
linked_spell(vengeance_16909.id, 200695, type=2)


vengeance_16910 = spell(
    id=16910,
    name='Vengeance',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=47,
    notes='pulled from existing data; druid-rework BALANCE §6 row (6,3). warlock-rework AFFLICTION §4.8 (A1/A2): linked to hidden passive 200696 (180%).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spell critical strikes now deal 180% damage. This does not stack with other similar effects.\n\n|cFF9D9D9DCapstone Bonus: Your direct Arcane and Nature critical strikes have a 15% chance to attract a Vengeful Soul, increasing your magic damage by 8% for 12 sec. When it ends, the Soul leaves your body and restores 10% of your missing mana. Only one Vengeful Soul can be attracted at a time, and a new proc refreshes it.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)
linked_spell(vengeance_16910.id, 200696, type=2)


vengeance_16911 = spell(
    id=16911,
    name='Vengeance',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200343),
    ],
    spell_icon_id=47,
    notes='pulled from existing data; druid-rework BALANCE §6 row (6,3): final rank, carries the Vengeful Soul capstone proc (200343 buff, procs_on(16911, ...) in druid_talents.py, spell_dru_vengeful_soul, WP-B). warlock-rework AFFLICTION §4.8 (A1/A2): eff1 crit-damage SpellMod zeroed, linked to hidden passive 200697 (199.5%); eff2 (Vengeful Soul proc trigger) untouched - its DisableEffectsMask 0x1 still validates because eff1 stays an aura.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spell critical strikes now deal 200% damage. This does not stack with other similar effects.\n\nCapstone Bonus: Your direct Arcane and Nature critical strikes have a 15% chance to attract a Vengeful Soul, increasing your magic damage by 8% for 12 sec. When it ends, the Soul leaves your body and restores 10% of your missing mana. Only one Vengeful Soul can be attracted at a time, and a new proc refreshes it.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)
linked_spell(vengeance_16911.id, 200697, type=2)


vengeance_16912 = spell(
    id=16912,
    name='Vengeance',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=79, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=47,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of your Starfire, Starfall, Moonfire, and Wrath spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 7, 'EffectSpellClassMaskA_2': 8388608, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


vengeance_16913 = spell(
    id=16913,
    name='Vengeance',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=47,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of your Starfire, Starfall, Moonfire, and Wrath spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 7, 'EffectSpellClassMaskA_2': 8388608, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


celestial_focus_16923 = spell(
    id=16923,
    name='Celestial Focus',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.REDUCE_PUSHBACK),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL, misc_value=0),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200342),
    ],
    spell_icon_id=1485,
    notes='pulled from existing data; druid-rework BALANCE §6 row (3,2): final rank, carries the Shooting Stars capstone proc (200342 buff, procs_on(16923, ...) in druid_talents.py, spell_dru_shooting_stars TODO WP-B)',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell, ranged, and melee haste by $s2%. Reduces the pushback suffered from damaging attacks by $s1%.\n\nCapstone Bonus: Your Moonfire and Insect Swarm periodic damage has a chance to grant Shooting Stars, empowering your next Starsurge within 15 sec to not trigger its cooldown and be a guaranteed critical strike.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'ProcTypeMask': 0, 'RangeIndex': 1, 'SpellClassSet': 7},
)


celestial_focus_16924 = spell(
    id=16924,
    name='Celestial Focus',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=69, implicit_target_a=1, apply_aura=108, misc_value=9),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=65, misc_value=9),
    ],
    spell_icon_id=1485,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the pushback suffered from damaging attacks while casting Starfire, Hibernate and Hurricane by $s1% and increases your total spell haste by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194308, 'EffectSpellClassMaskA_2': 131072, 'EffectSpellClassMaskB_1': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 15, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 7},
)


ferocity_16934 = spell(
    id=16934,
    name='Ferocity',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COST),
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COST),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=-1),
    ],
    spell_icon_id=1565,
    notes='druid-rework FERAL §7 (0,0), moved from (0,1): rank 1/5 - eff0 rage COST (Maul, Swipe (Bear), Mangle (Bear), Thrash) unchanged, eff1 energy COST retuned to -2..-10 (Rake, Mangle (Cat), Swipe (Cat); Claw dropped), new eff2 +1..5% all attributes.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all attributes by $s3%. Reduces the energy cost of your Swipe (Cat), Rake and Mangle (Cat) abilities by $s2 Energy. Reduces the rage cost of your Maul, Swipe (Bear), Thrash and Mangle (Bear) abilities by $/10;s1 Rage.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': MAUL, 'EffectSpellClassMaskA_2': SWIPE_BEAR | MANGLE_BEAR, 'EffectSpellClassMaskB_1': RAKE, 'EffectSpellClassMaskB_2': MANGLE_CAT, 'EffectSpellClassMaskB_3': SWIPE_CAT, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7, 'EffectSpellClassMaskA_3': THRASH},
)


ferocity_16935 = spell(
    id=16935,
    name='Ferocity',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COST),
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COST),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=-1),
    ],
    spell_icon_id=1565,
    notes='druid-rework FERAL §7 (0,0), moved from (0,1): rank 2/5 - eff0 rage COST (Maul, Swipe (Bear), Mangle (Bear), Thrash) unchanged, eff1 energy COST retuned to -2..-10 (Rake, Mangle (Cat), Swipe (Cat); Claw dropped), new eff2 +1..5% all attributes.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all attributes by $s3%. Reduces the energy cost of your Swipe (Cat), Rake and Mangle (Cat) abilities by $s2 Energy. Reduces the rage cost of your Maul, Swipe (Bear), Thrash and Mangle (Bear) abilities by $/10;s1 Rage.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': MAUL, 'EffectSpellClassMaskA_2': SWIPE_BEAR | MANGLE_BEAR, 'EffectSpellClassMaskB_1': RAKE, 'EffectSpellClassMaskB_2': MANGLE_CAT, 'EffectSpellClassMaskB_3': SWIPE_CAT, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7, 'EffectSpellClassMaskA_3': THRASH},
)


ferocity_16936 = spell(
    id=16936,
    name='Ferocity',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COST),
        Effect(type=EffectType.APPLY_AURA, base_points=-7, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COST),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=-1),
    ],
    spell_icon_id=1565,
    notes='druid-rework FERAL §7 (0,0), moved from (0,1): rank 3/5 - eff0 rage COST (Maul, Swipe (Bear), Mangle (Bear), Thrash) unchanged, eff1 energy COST retuned to -2..-10 (Rake, Mangle (Cat), Swipe (Cat); Claw dropped), new eff2 +1..5% all attributes.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all attributes by $s3%. Reduces the energy cost of your Swipe (Cat), Rake and Mangle (Cat) abilities by $s2 Energy. Reduces the rage cost of your Maul, Swipe (Bear), Thrash and Mangle (Bear) abilities by $/10;s1 Rage.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': MAUL, 'EffectSpellClassMaskA_2': SWIPE_BEAR | MANGLE_BEAR, 'EffectSpellClassMaskB_1': RAKE, 'EffectSpellClassMaskB_2': MANGLE_CAT, 'EffectSpellClassMaskB_3': SWIPE_CAT, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7, 'EffectSpellClassMaskA_3': THRASH},
)


ferocity_16937 = spell(
    id=16937,
    name='Ferocity',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-41, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COST),
        Effect(type=EffectType.APPLY_AURA, base_points=-9, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COST),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=-1),
    ],
    spell_icon_id=1565,
    notes='druid-rework FERAL §7 (0,0), moved from (0,1): rank 4/5 - eff0 rage COST (Maul, Swipe (Bear), Mangle (Bear), Thrash) unchanged, eff1 energy COST retuned to -2..-10 (Rake, Mangle (Cat), Swipe (Cat); Claw dropped), new eff2 +1..5% all attributes.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all attributes by $s3%. Reduces the energy cost of your Swipe (Cat), Rake and Mangle (Cat) abilities by $s2 Energy. Reduces the rage cost of your Maul, Swipe (Bear), Thrash and Mangle (Bear) abilities by $/10;s1 Rage.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': MAUL, 'EffectSpellClassMaskA_2': SWIPE_BEAR | MANGLE_BEAR, 'EffectSpellClassMaskB_1': RAKE, 'EffectSpellClassMaskB_2': MANGLE_CAT, 'EffectSpellClassMaskB_3': SWIPE_CAT, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7, 'EffectSpellClassMaskA_3': THRASH},
)


ferocity_16938 = spell(
    id=16938,
    name='Ferocity',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COST),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COST),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=-1),
    ],
    spell_icon_id=1565,
    notes='druid-rework FERAL §7 (0,0), moved from (0,1): rank 5/5 - eff0 rage COST (Maul, Swipe (Bear), Mangle (Bear), Thrash) unchanged, eff1 energy COST retuned to -2..-10 (Rake, Mangle (Cat), Swipe (Cat); Claw dropped), new eff2 +1..5% all attributes.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all attributes by $s3%. Reduces the energy cost of your Swipe (Cat), Rake and Mangle (Cat) abilities by $s2 Energy. Reduces the rage cost of your Maul, Swipe (Bear), Thrash and Mangle (Bear) abilities by $/10;s1 Rage.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': MAUL, 'EffectSpellClassMaskA_2': SWIPE_BEAR | MANGLE_BEAR, 'EffectSpellClassMaskB_1': RAKE, 'EffectSpellClassMaskB_2': MANGLE_CAT, 'EffectSpellClassMaskB_3': SWIPE_CAT, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7, 'EffectSpellClassMaskA_3': THRASH},
)


brutal_impact_16940 = spell(
    id=16940,
    name='Brutal Impact',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=499, implicit_target_a=1, apply_aura=107, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=-15001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=473,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the stun duration of your Bash and Pounce abilities by $/1000;S1 sec and decreases the cooldown of Bash by $/1000;S2 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 139264, 'EffectSpellClassMaskB_1': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


brutal_impact_16941 = spell(
    id=16941,
    name='Brutal Impact',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=999, implicit_target_a=1, apply_aura=107, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=-30001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=473,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the stun duration of your Bash and Pounce abilities by $/1000;S1 sec and decreases the cooldown of Bash by $/1000;S2 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 139264, 'EffectSpellClassMaskB_1': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


feral_instinct_16947 = spell(
    id=16947,
    name='Feral Instinct',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=103,
    notes="druid-rework FERAL §7 (1,0): rank 1/3 - eff0 prowl-detection aura -> APPLY_AURA DUMMY 1% (all damage during Tiger's Fury; spell_dru_tiger_s_fury_feral casts 200431 with it as BP0), eff1 Swipe damage SpellMod now also covers Ravage. ShapeshiftMask 145 kept (WP-BRIEF §3).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage done by your Swipe and Ravage abilities by $s2%. Increases all damage you deal by $s1% while Tiger's Fury is active.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_2': SWIPE_BEAR, 'EffectSpellClassMaskB_3': SWIPE_CAT, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': SS_FERAL, 'SpellClassSet': 7, 'EffectSpellClassMaskB_1': RAVAGE},
)


feral_instinct_16948 = spell(
    id=16948,
    name='Feral Instinct',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=103,
    notes="druid-rework FERAL §7 (1,0): rank 2/3 - eff0 prowl-detection aura -> APPLY_AURA DUMMY 2% (all damage during Tiger's Fury; spell_dru_tiger_s_fury_feral casts 200431 with it as BP0), eff1 Swipe damage SpellMod now also covers Ravage. ShapeshiftMask 145 kept (WP-BRIEF §3).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage done by your Swipe and Ravage abilities by $s2%. Increases all damage you deal by $s1% while Tiger's Fury is active.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_2': SWIPE_BEAR, 'EffectSpellClassMaskB_3': SWIPE_CAT, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': SS_FERAL, 'SpellClassSet': 7, 'EffectSpellClassMaskB_1': RAVAGE},
)


feral_instinct_16949 = spell(
    id=16949,
    name='Feral Instinct',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=103,
    notes="druid-rework FERAL §7 (1,0): rank 3/3 - eff0 prowl-detection aura -> APPLY_AURA DUMMY 3% (all damage during Tiger's Fury; spell_dru_tiger_s_fury_feral casts 200431 with it as BP0), eff1 Swipe damage SpellMod now also covers Ravage. ShapeshiftMask 145 kept (WP-BRIEF §3).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage done by your Swipe and Ravage abilities by $s2%. Increases all damage you deal by $s1% while Tiger's Fury is active.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_2': SWIPE_BEAR, 'EffectSpellClassMaskB_3': SWIPE_CAT, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': SS_FERAL, 'SpellClassSet': 7, 'EffectSpellClassMaskB_1': RAVAGE},
)


shredding_attacks_16966 = spell(
    id=16966,
    name='Shredding Attacks',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-8, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COST),
    ],
    spell_icon_id=147,
    notes='druid-rework FERAL §7 (3,0): rank 1/2 - eff0 energy COST -7 on Shred and Ravage; eff1 (Lacerate rage) removed.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the energy cost of your Shred and Ravage abilities by $s1.\n\n|cFF9D9D9DCapstone Bonus: Using Shred or Ravage while behind a target applies Shredded Defense, increasing the Physical damage the target takes from you by $200428s1% for $200428d. Stacks up to $200428u times.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': SHRED | RAVAGE, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


shredding_attacks_16968 = spell(
    id=16968,
    name='Shredding Attacks',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-16, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COST),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=147,
    notes="druid-rework FERAL §7 (3,0): rank 2/2, capstone (spell_dru_shredding_attacks casts Shredded Defense 200428 from behind) - eff0 energy COST -15 on Shred and Ravage; eff1 APPLY_AURA DUMMY 5 (% per Shredded Defense stack, informational - the C++ reads 200428's own eff0).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the energy cost of your Shred and Ravage abilities by $s1.\n\nCapstone Bonus: Using Shred or Ravage while behind a target applies Shredded Defense, increasing the Physical damage the target takes from you by $200428s1% for $200428d. Stacks up to $200428u times.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': SHRED | RAVAGE, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


predatory_strikes_16972 = spell(
    id=16972,
    name='Predatory Strikes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-4, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COST),
        Effect(type=EffectType.APPLY_AURA, base_points=124, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.ADD_TARGET_TRIGGER, trigger_spell=69369),
    ],
    spell_icon_id=1563,
    notes="druid-rework FERAL §7 (3,1) + FERAL-ADDENDUM §3.4: rank 1/3 - eff0 (icon-1563 DUMMY the core's feral-AP block reads) -> energy COST -3/-6/-9 on Rip/Ferocious Bite/Savage Roar/Maim, eff1 DUMMY removed (CORE-AUDIT row 35: the stock AP loop now adds 0) then re-added as a new marker 124/249/374 (12.5/25/37.5% in tenths, off-by-one convention) - ADD_FLAT_MODIFIER SpellModOp.DAMAGE with no classmask (matches nothing), not DUMMY, because icon 1563 is CORE-AUDIT row 35's own poisoned-icon (lib/test_druid_inert_keys.py FERAL_RETIRED_DUMMY_ICONS) - a DUMMY aura here would reactivate the still-live stock feral-AP hardcode. Read by Druid::OnSwellSpent as the bear Tooth and Claw chance per Swell stack consumed, eff2 Predator's Swiftness trigger kept at 5/10/15% per combo point (69369 narrowed to Regrowth only, user override).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces the energy cost of your Cat Form finishing moves by $s1. Your Feral finishing moves have a $b3% chance per combo point spent to make your next Regrowth instant. Your Pulverize and Upheaval have a ${$s2/10}% chance per Swell stack consumed to grant Tooth and Claw.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectPointsPerCombo_3': 5.0, 'EffectSpellClassMaskC_1': 8388608, 'EffectSpellClassMaskC_2': 268435584, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7, 'EffectSpellClassMaskA_1': RIP_FEROCIOUS_BITE, 'EffectSpellClassMaskA_2': SAVAGE_ROAR | MAIM},
)


predatory_strikes_16974 = spell(
    id=16974,
    name='Predatory Strikes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-7, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COST),
        Effect(type=EffectType.APPLY_AURA, base_points=249, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.ADD_TARGET_TRIGGER, trigger_spell=69369),
    ],
    spell_icon_id=1563,
    notes="druid-rework FERAL §7 (3,1) + FERAL-ADDENDUM §3.4: rank 2/3 - eff0 (icon-1563 DUMMY the core's feral-AP block reads) -> energy COST -3/-6/-9 on Rip/Ferocious Bite/Savage Roar/Maim, eff1 DUMMY removed (CORE-AUDIT row 35: the stock AP loop now adds 0) then re-added as a new marker 124/249/374 (12.5/25/37.5% in tenths, off-by-one convention) - ADD_FLAT_MODIFIER SpellModOp.DAMAGE with no classmask (matches nothing), not DUMMY, because icon 1563 is CORE-AUDIT row 35's own poisoned-icon (lib/test_druid_inert_keys.py FERAL_RETIRED_DUMMY_ICONS) - a DUMMY aura here would reactivate the still-live stock feral-AP hardcode. Read by Druid::OnSwellSpent as the bear Tooth and Claw chance per Swell stack consumed, eff2 Predator's Swiftness trigger kept at 5/10/15% per combo point (69369 narrowed to Regrowth only, user override).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces the energy cost of your Cat Form finishing moves by $s1. Your Feral finishing moves have a $b3% chance per combo point spent to make your next Regrowth instant. Your Pulverize and Upheaval have a ${$s2/10}% chance per Swell stack consumed to grant Tooth and Claw.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectPointsPerCombo_3': 10.0, 'EffectSpellClassMaskC_1': 8388608, 'EffectSpellClassMaskC_2': 268435584, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7, 'EffectSpellClassMaskA_1': RIP_FEROCIOUS_BITE, 'EffectSpellClassMaskA_2': SAVAGE_ROAR | MAIM},
)


predatory_strikes_16975 = spell(
    id=16975,
    name='Predatory Strikes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-10, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COST),
        Effect(type=EffectType.APPLY_AURA, base_points=374, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.ADD_TARGET_TRIGGER, trigger_spell=69369),
    ],
    spell_icon_id=1563,
    notes="druid-rework FERAL §7 (3,1) + FERAL-ADDENDUM §3.4: rank 3/3 - eff0 (icon-1563 DUMMY the core's feral-AP block reads) -> energy COST -3/-6/-9 on Rip/Ferocious Bite/Savage Roar/Maim, eff1 DUMMY removed (CORE-AUDIT row 35: the stock AP loop now adds 0) then re-added as a new marker 124/249/374 (12.5/25/37.5% in tenths, off-by-one convention) - ADD_FLAT_MODIFIER SpellModOp.DAMAGE with no classmask (matches nothing), not DUMMY, because icon 1563 is CORE-AUDIT row 35's own poisoned-icon (lib/test_druid_inert_keys.py FERAL_RETIRED_DUMMY_ICONS) - a DUMMY aura here would reactivate the still-live stock feral-AP hardcode. Read by Druid::OnSwellSpent as the bear Tooth and Claw chance per Swell stack consumed, eff2 Predator's Swiftness trigger kept at 5/10/15% per combo point (69369 narrowed to Regrowth only, user override).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces the energy cost of your Cat Form finishing moves by $s1. Your Feral finishing moves have a $b3% chance per combo point spent to make your next Regrowth instant. Your Pulverize and Upheaval have a ${$s2/10}% chance per Swell stack consumed to grant Tooth and Claw.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectPointsPerCombo_3': 15.0, 'EffectSpellClassMaskC_1': 8388608, 'EffectSpellClassMaskC_2': 268435584, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7, 'EffectSpellClassMaskA_1': RIP_FEROCIOUS_BITE, 'EffectSpellClassMaskA_2': SAVAGE_ROAR | MAIM},
)


predator_s_swiftness_69369 = spell(
    id=69369,
    name="Predator's Swiftness",
    school=School.NORMAL,
    dispel=DispelType.MAGIC,
    attributes=33816576,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=10),
    ],
    spell_icon_id=1563,
    notes="druid-rework FERAL-ADDENDUM §3.4: pulled from npc.csv (was declared only there, stock A_1 "
          "0x10000661/A_2/A_3 covering most Nature spells) and narrowed to REGROWTH only, dword 1, dropping "
          "A_2/A_3 entirely (user override: Predatory Strikes'/Nurturing Instinct's instant-cast proc reaches "
          "Regrowth only, not Healing Touch or any other Nature spell). Mechanism unchanged (ADD_PCT_MODIFIER "
          "misc SPELLMOD_CASTING_TIME, -100%).",
    raw_overrides={'AttributesEx': 131072, 'AttributesEx3': 196608, 'AttributesEx4': 64, 'CastingTimeIndex': 1, 'InterruptFlags': 4, 'ProcTypeMask': 87376, 'ProcChance': 100, 'ProcCharges': 1, 'SpellLevel': 1, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': REGROWTH, 'SpellVisualID_1': 4040, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'When activated, your next Regrowth becomes an instant cast spell.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next Regrowth is instant.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 7, 'SpellClassMask_2': 524288, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


savage_fury_16998 = spell(
    id=16998,
    name='Savage Fury',
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
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=1531,
    notes="druid-rework FERAL §7 (1,1): rank 1/2 - 6/12% (was 10/20%): eff0 DAMAGE on Rake/Maul/Shred and both Mangles (Claw dropped), eff1 DOT on Rake's bleed, eff2 (EFFECT3 on the Mangles) removed.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage caused by your Rake, Shred, Mangle (Cat), Mangle (Bear) and Maul abilities by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': RAKE | MAUL | SHRED, 'EffectSpellClassMaskB_1': RAKE, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7, 'EffectSpellClassMaskA_2': MANGLE_CAT | MANGLE_BEAR},
)


savage_fury_16999 = spell(
    id=16999,
    name='Savage Fury',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=1531,
    notes="druid-rework FERAL §7 (1,1): rank 2/2 - 6/12% (was 10/20%): eff0 DAMAGE on Rake/Maul/Shred and both Mangles (Claw dropped), eff1 DOT on Rake's bleed, eff2 (EFFECT3 on the Mangles) removed.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage caused by your Rake, Shred, Mangle (Cat), Mangle (Bear) and Maul abilities by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': RAKE | MAUL | SHRED, 'EffectSpellClassMaskB_1': RAKE, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7, 'EffectSpellClassMaskA_2': MANGLE_CAT | MANGLE_BEAR},
)


feral_swiftness_17002 = spell(
    id=17002,
    name='Feral Swiftness',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-26, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COOLDOWN),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=67,
    notes='druid-rework FERAL §7 (2,0): rank 1/2 - eff0 cat speed aura -> -25% Survival Instincts cooldown SpellMod; eff1 APPLY_AURA DUMMY 10 = cat move speed % (bear gets half; form-boost 24867 BP0, WP-BRIEF §4 item 1). ShapeshiftMask 1 removed so the passive exists in every form (WP-BRIEF §3).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your movement speed by $s2% in Cat Form and by ${$m2/2}% in Bear Form. Reduces the cooldown of Survival Instincts by $s1%.\n\n|cFF9D9D9DCapstone Bonus: After using Feral Charge (Bear), your next Mangle (Bear) within $200433d costs no rage and its cooldown is reset. After using Feral Charge (Cat), your next Ravage within $200434d requires no stealth and costs no energy.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7, 'NameSubtext_Lang_enUS': '', 'EffectSpellClassMaskA_3': SURVIVAL_INSTINCTS},
)


leader_of_the_pack_17007 = spell(
    id=17007,
    name='Leader of the Pack',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=312,
    notes='druid-rework FERAL §7 (6,1): tooltip only - the 4% base-health heal now lives on 24932 eff1 (spell_dru_leader_of_the_pack_feral).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While in Cat, Bear or Dire Bear Form, increases ranged and melee critical strike chance of all party and raid members within $24932a1 yards by $24932s1%. Affected targets also heal themselves for $24932s2% of their base health when they land a direct damage critical strike with a melee or ranged attack, no more than once every 6 sec. Does not stack with other similar effects. Periodic damage does not trigger the heal.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7, 'NameSubtext_Lang_enUS': ''},
)


improved_mark_of_the_wild_17050 = spell(
    id=17050,
    name='Improved Mark of the Wild',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=137, misc_value=-1),
    ],
    spell_icon_id=123,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effects of your Mark of the Wild and Gift of the Wild spells by $s1%, and increases all of your total attributes by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


improved_mark_of_the_wild_17051 = spell(
    id=17051,
    name='Improved Mark of the Wild',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=108, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=137, misc_value=-1),
    ],
    spell_icon_id=123,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effects of your Mark of the Wild and Gift of the Wild spells by $s1%, and increases all of your total attributes by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


furor_17056 = spell(
    id=17056,
    name='Furor',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=12),
    ],
    spell_icon_id=238,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives you $s1% chance to gain $/10;17057s1 Rage when you shapeshift into Bear and Dire Bear Form, and you keep up to $s1 of your Energy when you shapeshift into Cat Form, and increases your total Intellect while in Moonkin form by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_3': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


furor_17058 = spell(
    id=17058,
    name='Furor',
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
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=107, misc_value=12),
    ],
    spell_icon_id=238,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives you $s1% chance to gain $/10;17057s1 Rage when you shapeshift into Bear and Dire Bear Form, and you keep up to $s1 of your Energy when you shapeshift into Cat Form, and increases your total Intellect while in Moonkin form by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_3': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


furor_17059 = spell(
    id=17059,
    name='Furor',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=59, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=107, misc_value=12),
    ],
    spell_icon_id=238,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives you $s1% chance to gain $/10;17057s1 Rage when you shapeshift into Bear and Dire Bear Form, and you keep up to $s1 of your Energy when you shapeshift into Cat Form, and increases your total Intellect while in Moonkin form by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_3': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


furor_17060 = spell(
    id=17060,
    name='Furor',
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
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=107, misc_value=12),
    ],
    spell_icon_id=238,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives you $s1% chance to gain $/10;17057s1 Rage when you shapeshift into Bear and Dire Bear Form, and you keep up to $s1 of your Energy when you shapeshift into Cat Form, and increases your total Intellect while in Moonkin form by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_3': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


furor_17061 = spell(
    id=17061,
    name='Furor',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=12),
    ],
    spell_icon_id=238,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives you $s1% chance to gain $/10;17057s1 Rage when you shapeshift into Bear and Dire Bear Form, and you keep up to $s1 of your Energy when you shapeshift into Cat Form, and increases your total Intellect while in Moonkin form by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_3': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


nature_s_focus_17063 = spell(
    id=17063,
    name="Nature's Focus",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=AuraType.REDUCE_PUSHBACK, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL),
    ],
    spell_icon_id=963,
    notes="druid-rework RESTO §8 (0,1): eff1 replaced with generic REDUCE_PUSHBACK (149) misc 127 (all casts/channels, Spell.cpp:8119/8161, Q31 - unscoped rather than druid-only, matching the spec's wording); new eff2 HASTE_ALL (193). Capstone tooltip realized on Tranquility (740) itself via spell_dru_natures_focus_capstone.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell, ranged and melee haste by $s2%. Reduces pushback from damaging attacks while casting by $s1%.\n\n|cFF9D9D9DCapstone Bonus: While channeling Tranquility, you take 50% less damage and cannot be knocked back.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


nature_s_focus_17065 = spell(
    id=17065,
    name="Nature's Focus",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.REDUCE_PUSHBACK, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL),
    ],
    spell_icon_id=963,
    notes='druid-rework RESTO §8 (0,1): rank 2 (final/capstone rank) of the rewrite above.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell, ranged and melee haste by $s2%. Reduces pushback from damaging attacks while casting by $s1%.\n\nCapstone Bonus: While channeling Tranquility, you take 50% less damage and cannot be knocked back.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


nature_s_focus_17066 = spell(
    id=17066,
    name="Nature's Focus",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=69, implicit_target_a=1, apply_aura=108, misc_value=9),
    ],
    spell_icon_id=963,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the pushback suffered from damaging attacks  while casting Healing Touch, Wrath, Entangling Roots, Cyclone, Nourish, Regrowth and Tranquility by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 737, 'EffectSpellClassMaskA_2': 33554464, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


naturalist_17069 = spell(
    id=17069,
    name='Naturalist',
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
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CRITICAL_CHANCE),
    ],
    spell_icon_id=962,
    notes='druid-rework RESTO §8 (4,0), moved from (1,0), trimmed 5->3 ranks (17072/17073 orphaned): eff1 replaced with flat CRITICAL_CHANCE scoped to Healing Touch (A_1) and Swiftmend (A_2); the stock physical-damage-in-forms clause (old eff2) is removed.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the critical strike chance of your Healing Touch and Swiftmend by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Your direct Nature healing spells benefit from Mastery: Harmony, increasing their healing by 20% of Mastery for each of your heal over time effects on the target. Healing Touch benefits at twice the rate.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': HEALING_TOUCH, 'EffectSpellClassMaskA_2': SWIFTMEND, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


naturalist_17070 = spell(
    id=17070,
    name='Naturalist',
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
    ],
    spell_icon_id=962,
    notes='druid-rework RESTO §8 (4,0): rank 2 of the rewrite above.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the critical strike chance of your Healing Touch and Swiftmend by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Your direct Nature healing spells benefit from Mastery: Harmony, increasing their healing by 20% of Mastery for each of your heal over time effects on the target. Healing Touch benefits at twice the rate.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': HEALING_TOUCH, 'EffectSpellClassMaskA_2': SWIFTMEND, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


naturalist_17071 = spell(
    id=17071,
    name='Naturalist',
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
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CRITICAL_CHANCE),
        Effect(type=EffectType.DUMMY, base_points=0, implicit_target_a=1),
    ],
    spell_icon_id=962,
    notes='druid-rework RESTO §8 (4,0): rank 3, the final/capstone rank of the rewrite above - Harmony hook (Druid::GetHarmonyCoefficient reads this rank id), Healing Touch benefits at 0.40 instead of 0.20 per HoT.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the critical strike chance of your Healing Touch and Swiftmend by $s1%.\n\nCapstone Bonus: Your direct Nature healing spells benefit from Mastery: Harmony, increasing their healing by 20% of Mastery for each of your heal over time effects on the target. Healing Touch benefits at twice the rate.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': HEALING_TOUCH, 'EffectSpellClassMaskA_2': SWIFTMEND, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


naturalist_17072 = spell(
    id=17072,
    name='Naturalist',
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
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=79, misc_value=1),
    ],
    spell_icon_id=962,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cast time of your Healing Touch spell by $/1000;S1 sec and increases the damage you deal with physical attacks in all forms by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectItemType_1': 32, 'EffectSpellClassMaskA_1': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


naturalist_17073 = spell(
    id=17073,
    name='Naturalist',
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
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=79, misc_value=1),
    ],
    spell_icon_id=962,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cast time of your Healing Touch spell by $/1000;S1 sec and increases the damage you deal with physical attacks in all forms by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectItemType_1': 32, 'EffectSpellClassMaskA_1': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


nature_s_bounty_17074 = spell(
    id=17074,
    name="Nature's Bounty",
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
    ],
    spell_icon_id=197,
    notes="druid-rework RESTO §8 (5,2), trimmed 5->3 ranks (17077/17078 orphaned): eff1 keeps the stock ADD_FLAT_MODIFIER CRITICAL_CHANCE SpellMod (classmask trimmed to REGROWTH only, Nourish's bit dropped). Code-review fix: a prior rewrite replaced this with a plain DUMMY marker meant for a since-deleted Druid::ApplySpellCritChanceMods function, silently losing Regrowth's crit bonus entirely. The real mechanism (spell_dru_regrowth::CalculateTickAmount, CORE-AUDIT row 13) already reads this same effect via GetRankAmount(EFFECT_0) to subtract the bonus back out of the periodic tick's snapshotted crit chance (a raw classmask SpellMod bleeds into the HoT tick too) - direct Regrowth crit only, once corrected.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the critical effect chance of your Regrowth's direct heal by $s1%.\n\n|cFF9D9D9DCapstone Bonus: When your Regrowth's direct heal is a critical heal, you apply Regrowth's heal over time to one additional target.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': REGROWTH, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


nature_s_bounty_17075 = spell(
    id=17075,
    name="Nature's Bounty",
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
    ],
    spell_icon_id=197,
    notes='druid-rework RESTO §8 (5,2): rank 2 of the rewrite above.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the critical effect chance of your Regrowth's direct heal by $s1%.\n\n|cFF9D9D9DCapstone Bonus: When your Regrowth's direct heal is a critical heal, you apply Regrowth's heal over time to one additional target.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': REGROWTH, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


nature_s_bounty_17076 = spell(
    id=17076,
    name="Nature's Bounty",
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
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=197,
    notes='druid-rework RESTO §8 (5,2): rank 3, the final/capstone rank - new eff2 is the capstone-proc flag spell_dru_natures_bounty_capstone OnEffectProc reads (EFFECT_1, SPELL_AURA_DUMMY); procs_on(17076, ...) below registers when it fires.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the critical effect chance of your Regrowth's direct heal by $s1%.\n\nCapstone Bonus: When your Regrowth's direct heal is a critical heal, you apply Regrowth's heal over time to one additional target.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': REGROWTH, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)
procs_on(nature_s_bounty_17076, proc_flags=PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS, family_name=7,
         family_mask=(REGROWTH, 0, 0), spell_type_mask=PROC_SPELL_TYPE_HEAL,
         spell_phase_mask=PROC_SPELL_PHASE_HIT, hit_mask=PROC_HIT_CRITICAL, chance=100)


nature_s_bounty_17077 = spell(
    id=17077,
    name="Nature's Bounty",
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
    ],
    spell_icon_id=197,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical effect chance of your Regrowth and Nourish spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 64, 'EffectSpellClassMaskA_2': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


nature_s_bounty_17078 = spell(
    id=17078,
    name="Nature's Bounty",
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
    spell_icon_id=197,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical effect chance of your Regrowth and Nourish spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 64, 'EffectSpellClassMaskA_2': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


gift_of_nature_17104 = spell(
    id=17104,
    name='Gift of Nature',
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
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=266,
    notes="druid-rework RESTO §8 (4,1), trimmed 5->3 ranks (24945/24946 orphaned): re-scoped to HEAL_DIRECT (eff1, DAMAGE)/HEAL_DOT (eff2, DOT); stored value corrected to the design's 2/5/8 (the live pulled value was stale at 1/3/5).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effect of all Nature healing spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': HEAL_DIRECT[0], 'EffectSpellClassMaskA_2': HEAL_DIRECT[1], 'EffectSpellClassMaskA_3': HEAL_DIRECT[2], 'EffectSpellClassMaskB_1': HEAL_DOT[0], 'EffectSpellClassMaskB_2': HEAL_DOT[1], 'EffectSpellClassMaskB_3': HEAL_DOT[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


intensity_17106 = spell(
    id=17106,
    name='Intensity',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=16, implicit_target_a=1, apply_aura=134),
    ],
    spell_icon_id=101,
    notes="druid-rework RESTO §8 (2,0) / §0.13 Q3: stored value already matched (16 -> live 17, the stock number - 'not the spec's 16'); the Enrage PROC_TRIGGER_SPELL eff2 is removed and ProcTypeMask zeroed (dead without a rogue-style Enrage on this server) - non-stacking (A7) is a server-wide spell_group, not a data change here.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Allows $s1% of your mana regeneration to continue while casting. This effect does not stack with similar effects.\n\n|cFF9D9D9DCapstone Bonus: Your Mastery rating is increased by 15% of your Spirit.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'ProcTypeMask': 0, 'RangeIndex': 1, 'SpellClassSet': 7},
)


intensity_17107 = spell(
    id=17107,
    name='Intensity',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=1, apply_aura=134),
    ],
    spell_icon_id=101,
    notes='druid-rework RESTO §8 (2,0): rank 2 of the rewrite above.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Allows $s1% of your mana regeneration to continue while casting. This effect does not stack with similar effects.\n\n|cFF9D9D9DCapstone Bonus: Your Mastery rating is increased by 15% of your Spirit.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'ProcTypeMask': 0, 'RangeIndex': 1, 'SpellClassSet': 7},
)


intensity_17108 = spell(
    id=17108,
    name='Intensity',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=134),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.MOD_RATING_FROM_STAT, misc_value=1048576),
    ],
    spell_icon_id=101,
    notes="druid-rework RESTO §8 (2,0): rank 3, the final/capstone rank - new eff2 MOD_RATING_FROM_STAT (220) misc 1<<20 (CR_MASTERY), EffectMiscValueB_2=4 (STAT_SPIRIT) so Mastery rating tracks 15% of total Spirit dynamically (StatSystem.cpp/PlayerUpdates.cpp), including Living Spirit's bonuses.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Allows $s1% of your mana regeneration to continue while casting. This effect does not stack with similar effects.\n\nCapstone Bonus: Your Mastery rating is increased by 15% of your Spirit.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectMiscValueB_2': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'ProcTypeMask': 0, 'RangeIndex': 1, 'SpellClassSet': 7},
)


improved_rejuvenation_17111 = spell(
    id=17111,
    name='Improved Rejuvenation',
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
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=64,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effect of your Rejuvenation spell by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': 16, 'EffectSpellClassMaskB_2': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


improved_rejuvenation_17112 = spell(
    id=17112,
    name='Improved Rejuvenation',
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
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=64,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effect of your Rejuvenation spell by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


improved_rejuvenation_17113 = spell(
    id=17113,
    name='Improved Rejuvenation',
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
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=64,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effect of your Rejuvenation spell by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': 16, 'EffectSpellClassMaskB_2': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


subtlety_17118 = spell(
    id=17118,
    name='Subtlety',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=108, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=28),
    ],
    spell_icon_id=49,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the threat generated by your restoration spells by $s1% and reduces the chance your helpful spells, Moonfire, and Insect Swarm will be dispelled by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 262384, 'EffectSpellClassMaskA_2': 239603734, 'EffectSpellClassMaskB_1': 2359634, 'EffectSpellClassMaskB_2': 204214292, 'EffectSpellClassMaskB_3': 4096, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_3': 8192, 'SpellClassSet': 7},
)


subtlety_17119 = spell(
    id=17119,
    name='Subtlety',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=108, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=107, misc_value=28),
    ],
    spell_icon_id=49,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the threat generated by your restoration spells by $s1% and reduces the chance your helpful spells, Moonfire, and Insect Swarm will be dispelled by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 262384, 'EffectSpellClassMaskA_2': 235405334, 'EffectSpellClassMaskB_1': 2359634, 'EffectSpellClassMaskB_2': 204214292, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_3': 8192, 'SpellClassSet': 7},
)


subtlety_17120 = spell(
    id=17120,
    name='Subtlety',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=108, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=107, misc_value=28),
    ],
    spell_icon_id=49,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the threat generated by your restoration spells by $s1% and reduces the chance your helpful spells, Moonfire, and Insect Swarm will be dispelled by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 262384, 'EffectSpellClassMaskA_2': 239603734, 'EffectSpellClassMaskA_3': 8192, 'EffectSpellClassMaskB_1': 2359634, 'EffectSpellClassMaskB_2': 204214292, 'EffectSpellClassMaskB_3': 4096, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


improved_tranquility_17123 = spell(
    id=17123,
    name='Improved Tranquility',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=-30001, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COOLDOWN),
    ],
    spell_icon_id=100,
    notes='druid-rework RESTO §8 (4,3): eff1 replaces the stock threat mod with pct DAMAGE (reaches Tranquility tick 44203 via the shared TRANQUILITY bit); eff2 replaces the stock pct-cooldown mod with a flat COOLDOWN mod applied before Cooldown Haste (Player.cpp:11180-11186).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the healing of Tranquility by $s1% and reduces its cooldown by $/1000;s2 sec.\n\n|cFF9D9D9DCapstone Bonus: Tranquility benefits from Mastery: Harmony.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': TRANQUILITY, 'EffectSpellClassMaskB_1': TRANQUILITY, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


improved_tranquility_17124 = spell(
    id=17124,
    name='Improved Tranquility',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=-60001, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COOLDOWN),
    ],
    spell_icon_id=100,
    notes='druid-rework RESTO §8 (4,3): rank 2, the final/capstone rank of the rewrite above - Harmony hook (Druid::GetHarmonyCoefficient reads this rank id on Tranquility tick 44203).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the healing of Tranquility by $s1% and reduces its cooldown by $/1000;s2 sec.\n\nCapstone Bonus: Tranquility benefits from Mastery: Harmony.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': TRANQUILITY, 'EffectSpellClassMaskB_1': TRANQUILITY, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


feral_swiftness_24866 = spell(
    id=24866,
    name='Feral Swiftness',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COOLDOWN),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=67,
    notes='druid-rework FERAL §7 (2,0): rank 2/2, capstone (Stampede: spell_dru_feral_charge casts 200433/200434) - eff0 -50% Survival Instincts cooldown SpellMod; eff1 APPLY_AURA DUMMY 20 = cat move speed %. ShapeshiftMask removed.',
    raw_overrides={'AttributesEx': 2147483648, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your movement speed by $s2% in Cat Form and by ${$m2/2}% in Bear Form. Reduces the cooldown of Survival Instincts by $s1%.\n\nCapstone Bonus: After using Feral Charge (Bear), your next Mangle (Bear) within $200433d costs no rage and its cooldown is reset. After using Feral Charge (Cat), your next Ravage within $200434d requires no stealth and costs no energy.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7, 'NameSubtext_Lang_enUS': '', 'EffectSpellClassMaskA_3': SURVIVAL_INSTINCTS},
)


gift_of_nature_24943 = spell(
    id=24943,
    name='Gift of Nature',
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
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=266,
    notes="druid-rework RESTO §8 (4,1): rank 2 of the rewrite above.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effect of all Nature healing spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': HEAL_DIRECT[0], 'EffectSpellClassMaskA_2': HEAL_DIRECT[1], 'EffectSpellClassMaskA_3': HEAL_DIRECT[2], 'EffectSpellClassMaskB_1': HEAL_DOT[0], 'EffectSpellClassMaskB_2': HEAL_DOT[1], 'EffectSpellClassMaskB_3': HEAL_DOT[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


gift_of_nature_24944 = spell(
    id=24944,
    name='Gift of Nature',
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
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=266,
    notes="druid-rework RESTO §8 (4,1): rank 3 of the rewrite above.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effect of all Nature healing spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': HEAL_DIRECT[0], 'EffectSpellClassMaskA_2': HEAL_DIRECT[1], 'EffectSpellClassMaskA_3': HEAL_DIRECT[2], 'EffectSpellClassMaskB_1': HEAL_DOT[0], 'EffectSpellClassMaskB_2': HEAL_DOT[1], 'EffectSpellClassMaskB_3': HEAL_DOT[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


gift_of_nature_24945 = spell(
    id=24945,
    name='Gift of Nature',
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
    spell_icon_id=266,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effect of all healing spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 224, 'EffectSpellClassMaskA_2': 33554448, 'EffectSpellClassMaskB_1': 80, 'EffectSpellClassMaskB_2': 67108880, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


gift_of_nature_24946 = spell(
    id=24946,
    name='Gift of Nature',
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
    spell_icon_id=266,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effect of all healing spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 224, 'EffectSpellClassMaskA_2': 33554448, 'EffectSpellClassMaskB_1': 80, 'EffectSpellClassMaskB_2': 67108880, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


tranquil_spirit_24968 = spell(
    id=24968,
    name='Tranquil Spirit',
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
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=1714,
    notes="druid-rework RESTO §8 (3,1), trimmed 5->3 ranks (24971/24972 orphaned): eff1 rescoped to DIRECT_NATURE_HEAL (COST); new eff2 DAMAGE, same mask (Regrowth only gains on its direct part - DAMAGE never touches the DOT). Code-review-pass fix: this talent had been left half-implemented - eff1's base_points was still the untouched stock value (-3, delivering -2% instead of RESTO.md row 598's authoritative -7%) and eff2 didn't exist in the effects list at all, even though raw_overrides already carried EffectSpellClassMaskB_*/EffectBonusMultiplier_2 for it (prepared but never used) and the tooltip's own '$s2%' token had nothing to substitute. Both now match RESTO.md/docs/reworks/druid-resto.md's -7/-14/-20% cost, +2/4/6% healing progression.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your direct Nature healing spells by $s1% and increases their healing by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': DIRECT_NATURE_HEAL[0], 'EffectSpellClassMaskA_2': DIRECT_NATURE_HEAL[1], 'EffectSpellClassMaskA_3': DIRECT_NATURE_HEAL[2], 'EffectSpellClassMaskB_1': DIRECT_NATURE_HEAL[0], 'EffectSpellClassMaskB_2': DIRECT_NATURE_HEAL[1], 'EffectSpellClassMaskB_3': DIRECT_NATURE_HEAL[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


tranquil_spirit_24969 = spell(
    id=24969,
    name='Tranquil Spirit',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-15, implicit_target_a=1, apply_aura=108, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=1714,
    notes='druid-rework RESTO §8 (3,1): rank 2 of the rewrite above.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your direct Nature healing spells by $s1% and increases their healing by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': DIRECT_NATURE_HEAL[0], 'EffectSpellClassMaskA_2': DIRECT_NATURE_HEAL[1], 'EffectSpellClassMaskA_3': DIRECT_NATURE_HEAL[2], 'EffectSpellClassMaskB_1': DIRECT_NATURE_HEAL[0], 'EffectSpellClassMaskB_2': DIRECT_NATURE_HEAL[1], 'EffectSpellClassMaskB_3': DIRECT_NATURE_HEAL[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


tranquil_spirit_24970 = spell(
    id=24970,
    name='Tranquil Spirit',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=108, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=1714,
    notes='druid-rework RESTO §8 (3,1): rank 3 of the rewrite above.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your direct Nature healing spells by $s1% and increases their healing by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': DIRECT_NATURE_HEAL[0], 'EffectSpellClassMaskA_2': DIRECT_NATURE_HEAL[1], 'EffectSpellClassMaskA_3': DIRECT_NATURE_HEAL[2], 'EffectSpellClassMaskB_1': DIRECT_NATURE_HEAL[0], 'EffectSpellClassMaskB_2': DIRECT_NATURE_HEAL[1], 'EffectSpellClassMaskB_3': DIRECT_NATURE_HEAL[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


tranquil_spirit_24971 = spell(
    id=24971,
    name='Tranquil Spirit',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-9, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=1714,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your Healing Touch, Nourish and Tranquility spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 160, 'EffectSpellClassMaskA_2': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


tranquil_spirit_24972 = spell(
    id=24972,
    name='Tranquil Spirit',
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
    spell_icon_id=1714,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your Healing Touch, Nourish and Tranquility spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 160, 'EffectSpellClassMaskA_2': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


lunar_guidance_33589 = spell(
    id=33589,
    name='Lunar Guidance',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=174, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=290, misc_value=0),
    ],
    spell_icon_id=2256,
    notes='pulled from existing data; druid-rework BALANCE §6 row (4,0): eff2 moved from healing-from-Int to MOD_CRIT_PCT(290), junk classmasks cleared',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your critical strike chance with all spells and abilities by $s2%, and your spell damage by $s1% of your Intellect.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 3, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


lunar_guidance_33590 = spell(
    id=33590,
    name='Lunar Guidance',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=174, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=290, misc_value=0),
    ],
    spell_icon_id=2256,
    notes='pulled from existing data; druid-rework BALANCE §6 row (4,0)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your critical strike chance with all spells and abilities by $s2%, and your spell damage by $s1% of your Intellect.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 3, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


lunar_guidance_33591 = spell(
    id=33591,
    name='Lunar Guidance',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=174, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=290, misc_value=0),
    ],
    spell_icon_id=2256,
    notes='pulled from existing data; druid-rework BALANCE §6 row (4,0)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your critical strike chance with all spells and abilities by $s2%, and your spell damage by $s1% of your Intellect.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 3, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


balance_of_power_33592 = spell(
    id=33592,
    name='Balance of Power',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=0),
    ],
    spell_icon_id=2247,
    notes='pulled from existing data; druid-rework BALANCE §6 row (5,2): display-value DUMMY, spell_dru_eclipse HandleProc casts 200347 with BP0 = this rank\'s eff1 amount (CORE-AUDIT row 6 - PLAN C1 accepted)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Entering an Eclipse increases your spell power by $s1% for 5 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


balance_of_power_33596 = spell(
    id=33596,
    name='Balance of Power',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=0),
    ],
    spell_icon_id=2247,
    notes='pulled from existing data; druid-rework BALANCE §6 row (5,2)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Entering an Eclipse increases your spell power by $s1% for 5 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


dreamstate_33597 = spell(
    id=33597,
    name='Dreamstate',
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
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=290, misc_value=0),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=5000),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=108, misc_value=SpellModOp.EFFECT1),
    ],
    spell_icon_id=2255,
    notes='pulled from existing data; druid-rework BALANCE §6 row (5,0): eff1 moved from mana-regen-from-Int to MOD_CRIT_PCT(290); new eff2 is a PERIODIC_DUMMY the AuraScript reads to energize missing mana; new eff3 boosts Innervate (spell_dru_dreamstate/_dreamstate_innervate, WP-B)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your critical strike chance with all spells and abilities by $s1%. Regenerates $s2% of your missing mana every 5 sec. Innervate restores $s3% more mana.\n\n|cFF9D9D9DCapstone Bonus: Casting Innervate on another target also casts it on yourself.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskC_2': INNERVATE, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


dreamstate_33599 = spell(
    id=33599,
    name='Dreamstate',
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
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=290, misc_value=0),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=5000),
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=108, misc_value=SpellModOp.EFFECT1),
    ],
    spell_icon_id=2255,
    notes='pulled from existing data; druid-rework BALANCE §6 row (5,0)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your critical strike chance with all spells and abilities by $s1%. Regenerates $s2% of your missing mana every 5 sec. Innervate restores $s3% more mana.\n\n|cFF9D9D9DCapstone Bonus: Casting Innervate on another target also casts it on yourself.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskC_2': INNERVATE, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


improved_faerie_fire_33600 = spell(
    id=33600,
    name='Improved Faerie Fire',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=107, misc_value=23),
    ],
    spell_icon_id=109,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Faerie Fire spell also increases the chance the target will be hit by spell attacks by $s2%, and increases the critical strike chance of your damage spells by $s1% on targets afflicted by Faerie Fire.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1024, 'EffectSpellClassMaskB_1': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


improved_faerie_fire_33601 = spell(
    id=33601,
    name='Improved Faerie Fire',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=23),
    ],
    spell_icon_id=109,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Faerie Fire spell also increases the chance the target will be hit by spell attacks by $s2%, and increases the critical strike chance of your damage spells by $s1% on targets afflicted by Faerie Fire.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1024, 'EffectSpellClassMaskB_1': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


improved_faerie_fire_33602 = spell(
    id=33602,
    name='Improved Faerie Fire',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=107, misc_value=23),
    ],
    spell_icon_id=109,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Faerie Fire spell also increases the chance the target will be hit by spell attacks by $s2%, and increases the critical strike chance of your damage spells by $s1% on targets afflicted by Faerie Fire.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1024, 'EffectSpellClassMaskB_1': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


wrath_of_cenarius_33603 = spell(
    id=33603,
    name='Wrath of Cenarius',
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
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.BONUS_MULTIPLIER),
    ],
    spell_icon_id=2248,
    notes='pulled from existing data; druid-rework BALANCE §6 row (7,2): eff1 moved from a flat to a percent BONUS_MULTIPLIER SpellMod re-scoped to Starfire/Wrath/Starsurge; eff2 dropped',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the spell damage scaling of your Starfire, Wrath, and Starsurge by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Dealing damage with your Wrath reduces the remaining cooldown of your Solar Beam by 1 sec, and extends Nature\'s Grace by 0.5 sec.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': 5, 'EffectSpellClassMaskA_3': STARSURGE, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


wrath_of_cenarius_33604 = spell(
    id=33604,
    name='Wrath of Cenarius',
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
        Effect(type=EffectType.APPLY_AURA, base_points=13, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.BONUS_MULTIPLIER),
    ],
    spell_icon_id=2248,
    notes='pulled from existing data; druid-rework BALANCE §6 row (7,2)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the spell damage scaling of your Starfire, Wrath, and Starsurge by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Dealing damage with your Wrath reduces the remaining cooldown of your Solar Beam by 1 sec, and extends Nature\'s Grace by 0.5 sec.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': 5, 'EffectSpellClassMaskA_3': STARSURGE, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


wrath_of_cenarius_33605 = spell(
    id=33605,
    name='Wrath of Cenarius',
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
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.BONUS_MULTIPLIER),
    ],
    spell_icon_id=2248,
    notes='pulled from existing data; druid-rework BALANCE §6 row (7,2): final rank, carries the capstone (spell_dru_wrath_of_cenarius_capstone on 5176, WP-B)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the spell damage scaling of your Starfire, Wrath, and Starsurge by $s1%.\n\nCapstone Bonus: Dealing damage with your Wrath reduces the remaining cooldown of your Solar Beam by 1 sec, and extends Nature\'s Grace by 0.5 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': 5, 'EffectSpellClassMaskA_3': STARSURGE, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


wrath_of_cenarius_33606 = spell(
    id=33606,
    name='Wrath of Cenarius',
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
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=107, misc_value=24),
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=107, misc_value=24),
    ],
    spell_icon_id=2248,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Starfire spell gains an additional $s1% and your Wrath gains an additional $s2% of your bonus damage effects.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': 4, 'EffectSpellClassMaskB_1': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


wrath_of_cenarius_33607 = spell(
    id=33607,
    name='Wrath of Cenarius',
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
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=107, misc_value=24),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=24),
    ],
    spell_icon_id=2248,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Starfire spell gains an additional $s1% and your Wrath gains an additional $s2% of your bonus damage effects.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': 4, 'EffectSpellClassMaskB_1': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


primal_tenacity_33851 = spell(
    id=33851,
    name='Primal Tenacity',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=232, misc_value=5),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=69, misc_value=127),
    ],
    spell_icon_id=2253,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the duration of fear effects by $s1%, reduces all damage taken while stunned by $s2% while in Cat Form.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 33554432, 'EffectSpellClassMaskC_1': 3221225472, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


primal_tenacity_33852 = spell(
    id=33852,
    name='Primal Tenacity',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=232, misc_value=5),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=69, misc_value=127),
    ],
    spell_icon_id=2253,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the duration of fear effects by $s1%, reduces all damage taken while stunned by $s2% while in Cat Form.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 33554432, 'EffectSpellClassMaskC_1': 3221225472, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


survival_of_the_fittest_33853 = spell(
    id=33853,
    name='Survival of the Fittest',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=-1),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MOD_ATTACK_POWER_PCT),
    ],
    spell_icon_id=2253,
    notes='druid-rework FERAL §7 (5,2): rank 1/3 - eff0 all attributes 1/2/3%; eff1 crit-taken aura -> MOD_ATTACK_POWER_PCT 3/6/10% (spell_dru_survival_of_the_fittest zeroes it unless Bestial Fury); eff2 (stock armor DUMMY) removed; ShapeshiftMask 0 -> both bears; icon 961 -> 2253 (Ability_Druid_PrimalTenacity, freed by the Primal Tenacity cut) so the stock icon-961 aura-137 block goes inert (CORE-AUDIT row 32).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While you are in Bear Form or Dire Bear Form, increases all attributes by $s1%. While Bestial Fury is active, increases your attack power by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7, 'ShapeshiftMask': SS_ANY_BEAR},
)


survival_of_the_fittest_33855 = spell(
    id=33855,
    name='Survival of the Fittest',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=-1),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.MOD_ATTACK_POWER_PCT),
    ],
    spell_icon_id=2253,
    notes='druid-rework FERAL §7 (5,2): rank 2/3 - eff0 all attributes 1/2/3%; eff1 crit-taken aura -> MOD_ATTACK_POWER_PCT 3/6/10% (spell_dru_survival_of_the_fittest zeroes it unless Bestial Fury); eff2 (stock armor DUMMY) removed; ShapeshiftMask 0 -> both bears; icon 961 -> 2253 (Ability_Druid_PrimalTenacity, freed by the Primal Tenacity cut) so the stock icon-961 aura-137 block goes inert (CORE-AUDIT row 32).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While you are in Bear Form or Dire Bear Form, increases all attributes by $s1%. While Bestial Fury is active, increases your attack power by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7, 'ShapeshiftMask': SS_ANY_BEAR},
)


survival_of_the_fittest_33856 = spell(
    id=33856,
    name='Survival of the Fittest',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=-1),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.MOD_ATTACK_POWER_PCT),
    ],
    spell_icon_id=2253,
    notes='druid-rework FERAL §7 (5,2): rank 3/3 - eff0 all attributes 1/2/3%; eff1 crit-taken aura -> MOD_ATTACK_POWER_PCT 3/6/10% (spell_dru_survival_of_the_fittest zeroes it unless Bestial Fury); eff2 (stock armor DUMMY) removed; ShapeshiftMask 0 -> both bears; icon 961 -> 2253 (Ability_Druid_PrimalTenacity, freed by the Primal Tenacity cut) so the stock icon-961 aura-137 block goes inert (CORE-AUDIT row 32).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While you are in Bear Form or Dire Bear Form, increases all attributes by $s1%. While Bestial Fury is active, increases your attack power by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7, 'ShapeshiftMask': SS_ANY_BEAR},
)


predatory_instincts_33859 = spell(
    id=33859,
    name='Predatory Instincts',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_DAMAGE_BONUS, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=-4, implicit_target_a=1, apply_aura=AuraType.MOD_AOE_DAMAGE_AVOIDANCE, misc_value=127),
    ],
    spell_icon_id=2252,
    notes='druid-rework FERAL §7 (7,2) + CORE-AUDIT row 25 (C2 accepted): rank 1/3 - eff0 aura 163 misc 1 5/10/15 (x1.05/1.10/1.15 on the 200% crit = 210/220/230%; spell_dru_predatory_instincts zeroes it outside Cat Form, so bleed ticks in cat are boosted too - accepted deviation (a)); eff1 AoE damage taken -3/-6/-10%; ShapeshiftMask 1 removed (WP-BRIEF §3).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your critical strikes in Cat Form deal ${200+$m1*2}% damage instead of 200%. Reduces the damage taken from area of effect attacks by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


predatory_instincts_33866 = spell(
    id=33866,
    name='Predatory Instincts',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_DAMAGE_BONUS, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=-7, implicit_target_a=1, apply_aura=AuraType.MOD_AOE_DAMAGE_AVOIDANCE, misc_value=127),
    ],
    spell_icon_id=2252,
    notes='druid-rework FERAL §7 (7,2) + CORE-AUDIT row 25 (C2 accepted): rank 2/3 - eff0 aura 163 misc 1 5/10/15 (x1.05/1.10/1.15 on the 200% crit = 210/220/230%; spell_dru_predatory_instincts zeroes it outside Cat Form, so bleed ticks in cat are boosted too - accepted deviation (a)); eff1 AoE damage taken -3/-6/-10%; ShapeshiftMask 1 removed (WP-BRIEF §3).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your critical strikes in Cat Form deal ${200+$m1*2}% damage instead of 200%. Reduces the damage taken from area of effect attacks by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


predatory_instincts_33867 = spell(
    id=33867,
    name='Predatory Instincts',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_DAMAGE_BONUS, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=AuraType.MOD_AOE_DAMAGE_AVOIDANCE, misc_value=127),
    ],
    spell_icon_id=2252,
    notes='druid-rework FERAL §7 (7,2) + CORE-AUDIT row 25 (C2 accepted): rank 3/3 - eff0 aura 163 misc 1 5/10/15 (x1.05/1.10/1.15 on the 200% crit = 210/220/230%; spell_dru_predatory_instincts zeroes it outside Cat Form, so bleed ticks in cat are boosted too - accepted deviation (a)); eff1 AoE damage taken -3/-6/-10%; ShapeshiftMask 1 removed (WP-BRIEF §3).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your critical strikes in Cat Form deal ${200+$m1*2}% damage instead of 200%. Reduces the damage taken from area of effect attacks by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


nurturing_instinct_33872 = spell(
    id=33872,
    name='Nurturing Instinct',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2254,
    notes="druid-rework FERAL §7 (4,3) + FERAL-ADDENDUM §3.8: rank 1/2 - eff0 aura 175 -> APPLY_AURA DUMMY 5/10% healing received from other players in cat/bear/dire bear (CORE-AUDIT row 26 hook; the stock icon-2254 aura-175 block goes inert, row 32); new eff1 APPLY_AURA DUMMY 15/30% (BP0/BP1 of the 200430 buff), now triggered by a Predator's-Swiftness Regrowth (not Healing Touch, user override) or by Savage Bite (200439, shares Pulverize's family bit so it needs no extra mask).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases healing done to you by other players by $s1% while in Cat, Bear and Dire Bear Form. When you cast Regrowth made instant by Predatory Strikes, or when you use Savage Bite, your next $200430n melee abilities within $200430d deal $s2% increased damage.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


nurturing_instinct_33873 = spell(
    id=33873,
    name='Nurturing Instinct',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2254,
    notes="druid-rework FERAL §7 (4,3) + FERAL-ADDENDUM §3.8: rank 2/2 - eff0 aura 175 -> APPLY_AURA DUMMY 5/10% healing received from other players in cat/bear/dire bear (CORE-AUDIT row 26 hook; the stock icon-2254 aura-175 block goes inert, row 32); new eff1 APPLY_AURA DUMMY 15/30% (BP0/BP1 of the 200430 buff), now triggered by a Predator's-Swiftness Regrowth (not Healing Touch, user override) or by Savage Bite (200439, shares Pulverize's family bit so it needs no extra mask).",
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases healing done to you by other players by $s1% while in Cat, Bear and Dire Bear Form. When you cast Regrowth made instant by Predatory Strikes, or when you use Savage Bite, your next $200430n melee abilities within $200430d deal $s2% increased damage.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


empowered_touch_33879 = spell(
    id=33879,
    name='Empowered Touch',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.BONUS_MULTIPLIER),
    ],
    spell_icon_id=2251,
    notes='druid-rework RESTO §8 (5,0): drops the Nourish eff2 (Nourish is removed); eff1 kept, scoped to Healing Touch only.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your Healing Touch gains an additional $s1% of your bonus healing effects.\n\n|cFF9D9D9DCapstone Bonus: Your Healing Touch and Flourish casts reduce the remaining cooldown of Natural Alacrity and Tranquility by 2 sec.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': HEALING_TOUCH, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


empowered_touch_33880 = spell(
    id=33880,
    name='Empowered Touch',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.BONUS_MULTIPLIER),
        Effect(type=EffectType.DUMMY, base_points=1999, implicit_target_a=1),
    ],
    spell_icon_id=2251,
    notes='druid-rework RESTO §8 (5,0): rank 2, the final/capstone rank - new eff2 DUMMY stored 1999 (the 2 sec cooldown reduction); spell_dru_empowered_touch_capstone (bound to 5185 and 200564) reads this rank id and calls Druid::ReduceSpellCooldown on Natural Alacrity (17116) and Tranquility (740) after a qualifying cast.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your Healing Touch gains an additional $s1% of your bonus healing effects.\n\nCapstone Bonus: Your Healing Touch and Flourish casts reduce the remaining cooldown of Natural Alacrity and Tranquility by 2 sec.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': HEALING_TOUCH, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


natural_perfection_33881 = spell(
    id=33881,
    name='Natural Perfection',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_PCT),
    ],
    spell_icon_id=2250,
    notes='druid-rework RESTO §8 (6,2): removes the stock crit-taken proc (eff1); eff2 (now eff1) generalized from MOD_SPELL_CRIT_CHANCE (57) to MOD_CRIT_PCT (290, all crit, PLAN §2 generalized-stat rule, Q13). ProcTypeMask zeroed - no proc-capable effect on r1/r2.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your critical strike chance with all spells is increased by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Your critical heals from direct Nature healing spells reduce the remaining cooldown of Cenarion Ward by 2 sec.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'ProcTypeMask': 0, 'RangeIndex': 1, 'SpellClassSet': 7},
)


natural_perfection_33882 = spell(
    id=33882,
    name='Natural Perfection',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_PCT),
    ],
    spell_icon_id=2250,
    notes='druid-rework RESTO §8 (6,2): rank 2 of the rewrite above.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your critical strike chance with all spells is increased by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Your critical heals from direct Nature healing spells reduce the remaining cooldown of Cenarion Ward by 2 sec.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'ProcTypeMask': 0, 'RangeIndex': 1, 'SpellClassSet': 7},
)


natural_perfection_33883 = spell(
    id=33883,
    name='Natural Perfection',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=1999, implicit_target_a=1),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_PCT),
    ],
    spell_icon_id=2250,
    notes="druid-rework RESTO §8 (6,2): rank 3, the final/capstone rank - eff1 DUMMY stored 1999 is cosmetic only (tooltip-matching 2 sec, not read by any script - spell_dru_natural_perfection_capstone hardcodes 2000 in its ReduceSpellCooldown call); harmless since eff2's real MOD_CRIT_PCT effect is what makes this spell create an Aura at all, and the whole-aura OnProc/DoCheckProc hooks below don't key off any specific effect index. negative procs_on(-33881, ...) below (stock -33881 precedent) fires spell_dru_natural_perfection_capstone's OnProc, which calls Druid::ReduceSpellCooldown(200562, 2000) after checking Heal::IsDirectNatureHeal.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your critical strike chance with all spells is increased by $s2%.\n\nCapstone Bonus: Your critical heals from direct Nature healing spells reduce the remaining cooldown of Cenarion Ward by 2 sec.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'ProcTypeMask': 0, 'RangeIndex': 1, 'SpellClassSet': 7},
)


empowered_rejuvenation_33886 = spell(
    id=33886,
    name='Empowered Rejuvenation',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=108, misc_value=24),
    ],
    spell_icon_id=2249,
    notes="druid-rework RESTO §8 (5,1), moved from (7,1), trimmed 5->3 ranks (33889/33890 orphaned): re-scoped to EMP_REJUV_COEFF (Rejuvenation/Germination shared bit, Lifebloom, Wild Growth, Cenarion Ward's released heal - Regrowth deliberately excluded, handled in C++ so BONUS_MULTIPLIER doesn't also scale Regrowth's direct coefficient).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "The bonus healing effects of your Rejuvenation, Lifebloom, Wild Growth, Regrowth's heal over time and Cenarion Ward are increased by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Your Rejuvenation, Lifebloom, Wild Growth, Regrowth's heal over time and Cenarion Ward benefit from Mastery: Harmony.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': EMP_REJUV_COEFF[0], 'EffectSpellClassMaskA_2': EMP_REJUV_COEFF[1], 'EffectSpellClassMaskA_3': EMP_REJUV_COEFF[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


empowered_rejuvenation_33887 = spell(
    id=33887,
    name='Empowered Rejuvenation',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=13, implicit_target_a=1, apply_aura=108, misc_value=24),
    ],
    spell_icon_id=2249,
    notes='druid-rework RESTO §8 (5,1): rank 2 of the rewrite above.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "The bonus healing effects of your Rejuvenation, Lifebloom, Wild Growth, Regrowth's heal over time and Cenarion Ward are increased by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Your Rejuvenation, Lifebloom, Wild Growth, Regrowth's heal over time and Cenarion Ward benefit from Mastery: Harmony.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': EMP_REJUV_COEFF[0], 'EffectSpellClassMaskA_2': EMP_REJUV_COEFF[1], 'EffectSpellClassMaskA_3': EMP_REJUV_COEFF[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


empowered_rejuvenation_33888 = spell(
    id=33888,
    name='Empowered Rejuvenation',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=24),
        Effect(type=EffectType.DUMMY, base_points=0, implicit_target_a=1),
    ],
    spell_icon_id=2249,
    notes='druid-rework RESTO §8 (5,1): rank 3, the final/capstone rank - new eff2 DUMMY stored 0 is the Harmony-enabled flag Druid::GetHarmonyCoefficient reads for the five listed spells.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "The bonus healing effects of your Rejuvenation, Lifebloom, Wild Growth, Regrowth's heal over time and Cenarion Ward are increased by $s1%.\n\nCapstone Bonus: Your Rejuvenation, Lifebloom, Wild Growth, Regrowth's heal over time and Cenarion Ward benefit from Mastery: Harmony.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': EMP_REJUV_COEFF[0], 'EffectSpellClassMaskA_2': EMP_REJUV_COEFF[1], 'EffectSpellClassMaskA_3': EMP_REJUV_COEFF[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


empowered_rejuvenation_33889 = spell(
    id=33889,
    name='Empowered Rejuvenation',
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
    ],
    spell_icon_id=2249,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The bonus healing effects of your healing over time spells is increased by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 208, 'EffectSpellClassMaskA_2': 67108880, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


empowered_rejuvenation_33890 = spell(
    id=33890,
    name='Empowered Rejuvenation',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=24),
    ],
    spell_icon_id=2249,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The bonus healing effects of your healing over time spells is increased by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 208, 'EffectSpellClassMaskA_2': 67108880, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


dreamstate_33956 = spell(
    id=33956,
    name='Dreamstate',
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
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=290, misc_value=0),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=5000),
        Effect(type=EffectType.APPLY_AURA, base_points=74, implicit_target_a=1, apply_aura=108, misc_value=SpellModOp.EFFECT1),
    ],
    spell_icon_id=2255,
    notes='pulled from existing data; druid-rework BALANCE §6 row (5,0): final rank, carries the self-Innervate capstone (spell_dru_dreamstate_innervate on 29166, WP-B)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your critical strike chance with all spells and abilities by $s1%. Regenerates $s2% of your missing mana every 5 sec. Innervate restores $s3% more mana.\n\nCapstone Bonus: Casting Innervate on another target also casts it on yourself.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskC_2': INNERVATE, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


primal_tenacity_33957 = spell(
    id=33957,
    name='Primal Tenacity',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=232, misc_value=5),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=69, misc_value=127),
    ],
    spell_icon_id=2253,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the duration of fear effects by $s1%, reduces all damage taken while stunned by $s2% while in Cat Form.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 33554432, 'EffectSpellClassMaskC_1': 3221225472, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


living_spirit_34151 = spell(
    id=34151,
    name='Living Spirit',
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
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=137, misc_value=4),
    ],
    spell_icon_id=2011,
    notes="druid-rework RESTO §8 (6,0): tooltip gains the capstone clause (rank 3 supplies the mechanic).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your total Spirit by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Your Spirit is increased by 1% for each of your active Rejuvenations, up to 10%.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


living_spirit_34152 = spell(
    id=34152,
    name='Living Spirit',
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
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=137, misc_value=4),
    ],
    spell_icon_id=2011,
    notes="druid-rework RESTO §8 (6,0): rank 2, tooltip only.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your total Spirit by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Your Spirit is increased by 1% for each of your active Rejuvenations, up to 10%.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


living_spirit_34153 = spell(
    id=34153,
    name='Living Spirit',
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
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=137, misc_value=4),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=1000),
    ],
    spell_icon_id=2011,
    notes='druid-rework RESTO §8 (6,0): rank 3, the final/capstone rank - new eff2 PERIODIC_DUMMY (1 s) drives spell_dru_living_spirit_capstone, which counts active Rejuvenations (Druid::CountActiveRejuvenations) and stacks/removes 200571.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your total Spirit by $s1%.\n\nCapstone Bonus: Your Spirit is increased by 1% for each of your active Rejuvenations, up to 10%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


improved_leader_of_the_pack_34297 = spell(
    id=34297,
    name='Improved Leader of the Pack',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=12),
        Effect(type=EffectType.DUMMY, base_points=3, implicit_target_a=1),
    ],
    spell_icon_id=312,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Leader of the Pack ability also causes affected targets to heal themselves for $s1% of their total health when they critically hit with a melee or ranged attack.  The healing effect cannot occur more than once every 6 sec.  In addition, you gain $s2% of your maximum mana when you benefit from this heal.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2048, 'EffectSpellClassMaskB_1': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


improved_leader_of_the_pack_34300 = spell(
    id=34300,
    name='Improved Leader of the Pack',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=107, misc_value=12),
        Effect(type=EffectType.DUMMY, base_points=7, implicit_target_a=1),
    ],
    spell_icon_id=312,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Leader of the Pack ability also causes affected targets to heal themselves for $s1% of their total health when they critically hit with a melee or ranged attack.  The healing effect cannot occur more than once every 6 sec.  In addition, you gain $s2% of your maximum mana when you benefit from this heal.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2048, 'EffectSpellClassMaskB_1': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


nature_s_majesty_35363 = spell(
    id=35363,
    name="Nature's Majesty",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CRITICAL_CHANCE),
        Effect(type=EffectType.APPLY_AURA, base_points=-5001, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COOLDOWN),
    ],
    spell_icon_id=598,
    notes='pulled from existing data; druid-rework BALANCE §6 row (1,1): +Starsurge to the crit mask, new eff2 cuts Mass Entanglement\'s cooldown. Tooltip drops Nourish (PLAN B8: Nourish is retired; its A_2 bit stays, harmless)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Wrath, Starfire, Starfall, Starsurge, and Healing Touch by $s1%. Reduces the cooldown of your Mass Entanglement by $/1000;s2 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 37, 'EffectSpellClassMaskA_2': 41943040, 'EffectSpellClassMaskA_3': STARSURGE, 'EffectSpellClassMaskB_3': MASS_ENTANGLEMENT, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


nature_s_majesty_35364 = spell(
    id=35364,
    name="Nature's Majesty",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CRITICAL_CHANCE),
        Effect(type=EffectType.APPLY_AURA, base_points=-10001, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COOLDOWN),
    ],
    spell_icon_id=598,
    notes='pulled from existing data; druid-rework BALANCE §6 row (1,1)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Wrath, Starfire, Starfall, Starsurge, and Healing Touch by $s1%. Reduces the cooldown of your Mass Entanglement by $/1000;s2 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 37, 'EffectSpellClassMaskA_2': 41943040, 'EffectSpellClassMaskA_3': STARSURGE, 'EffectSpellClassMaskB_3': MASS_ENTANGLEMENT, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


improved_moonkin_form_48384 = spell(
    id=48384,
    name='Improved Moonkin Form',
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
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=174, misc_value=126),
    ],
    spell_icon_id=2855,
    notes='pulled from existing data; druid-rework BALANCE §6 row (6,2): eff1\'s inert DUMMY cleared, eff2 doubled to 20/40/60% of Spirit',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Moonkin Aura also grants affected targets $50170s1% haste, and grants you $s2% of your Spirit as additional spell damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_2': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 1073741824, 'SpellClassSet': 7},
)


improved_moonkin_form_48395 = spell(
    id=48395,
    name='Improved Moonkin Form',
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
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=174, misc_value=126),
    ],
    spell_icon_id=2855,
    notes='pulled from existing data; druid-rework BALANCE §6 row (6,2)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Moonkin Aura also grants affected targets $50171s1% haste, and grants you $s2% of your Spirit as additional spell damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_2': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 1073741824, 'SpellClassSet': 7},
)


improved_moonkin_form_48396 = spell(
    id=48396,
    name='Improved Moonkin Form',
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
        Effect(type=EffectType.APPLY_AURA, base_points=59, implicit_target_a=1, apply_aura=174, misc_value=126),
    ],
    spell_icon_id=2855,
    notes='pulled from existing data; druid-rework BALANCE §6 row (6,2)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Moonkin Aura also grants affected targets $50172s1% haste, and grants you $s2% of your Spirit as additional spell damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_2': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 1073741824, 'SpellClassSet': 7},
)


primal_precision_48409 = spell(
    id=48409,
    name='Primal Precision',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.MOD_POWER_REGEN_PERCENT, misc_value=3),
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL),
    ],
    spell_icon_id=2858,
    notes="druid-rework FERAL §7 (3,3) + FERAL-ADDENDUM §3.7: rank 1/2 - expertise -> +10/20% energy regeneration (aura 110 misc 3 = POWER_ENERGY); finishing-move refund removed; new eff2 HASTE_ALL 5/10% (aura 193, misnamed SPELL_AURA_MELEE_SLOW in C++), zeroed outside Bestial Fury by spell_dru_primal_precision_haste (canBeRecalculated, recalculated by Druid::OnFeralFormChanged on every form change).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your energy regeneration rate by $s1%. While Bestial Fury is active, increases your haste by $s3%.\n\n|cFF9D9D9DCapstone Bonus: Your Cat Form finishing moves reduce the cooldown of Berserk by $48410s2 sec. Your Pulverize reduces the cooldown of Berserk by 10 sec, and your Savage Bite by 3 sec. These effects cannot occur more than once every 5 sec, and do not reduce the cooldown of Berserk while Berserk is active.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


primal_precision_48410 = spell(
    id=48410,
    name='Primal Precision',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.MOD_POWER_REGEN_PERCENT, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL),
    ],
    spell_icon_id=2858,
    notes="druid-rework FERAL §7 (3,3) + FERAL-ADDENDUM §3.7: rank 2/2 - expertise -> +10/20% energy regeneration (aura 110 misc 3 = POWER_ENERGY); finishing-move refund removed; capstone eff1 APPLY_AURA DUMMY 3 = seconds off Berserk per Cat Form finisher (spell_dru_primal_precision, now a shared 5 s ICD with the bear clause below, nothing while Berserk is active); new eff2 HASTE_ALL 5/10% (aura 193, misnamed SPELL_AURA_MELEE_SLOW in C++), zeroed outside Bestial Fury by spell_dru_primal_precision_haste; bear clause (Druid::TryPrimalPrecisionBearReduction, playtest revision - was 2 sec per Swell stack Pulverize/Upheaval consume) takes 10 sec off Berserk per Pulverize and 3 sec per Savage Bite, sharing this rank's 48410 ICD marker.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your energy regeneration rate by $s1%. While Bestial Fury is active, increases your haste by $s3%.\n\nCapstone Bonus: Your Cat Form finishing moves reduce the cooldown of Berserk by $48410s2 sec. Your Pulverize reduces the cooldown of Berserk by 10 sec, and your Savage Bite by 3 sec. These effects cannot occur more than once every 5 sec, and do not reduce the cooldown of Berserk while Berserk is active.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


rend_and_tear_48432 = spell(
    id=48432,
    name='Rend and Tear',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=494,
    notes="druid-rework FERAL §7 (9,1), trimmed 5->3 ranks: rank 1/3 - eff0 7/14/20% Maul/Shred damage, eff1 10/20/30% Ferocious Bite crit (BP0 of the CanPrepare helper 200436), both vs the caster's own Rip or Lacerate; icon 2859 -> 494 (Ability_Druid_Disembowel) so the stock any-bleed hardcodes go inert (CORE-AUDIT row 24).",
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Targets affected by your Rip or Lacerate make your Maul and Shred attacks deal $s1% more damage and increase the critical strike chance of your Ferocious Bite ability by $s2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 34816, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


rend_and_tear_48433 = spell(
    id=48433,
    name='Rend and Tear',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=13, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=494,
    notes="druid-rework FERAL §7 (9,1), trimmed 5->3 ranks: rank 2/3 - eff0 7/14/20% Maul/Shred damage, eff1 10/20/30% Ferocious Bite crit (BP0 of the CanPrepare helper 200436), both vs the caster's own Rip or Lacerate; icon 2859 -> 494 (Ability_Druid_Disembowel) so the stock any-bleed hardcodes go inert (CORE-AUDIT row 24).",
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Targets affected by your Rip or Lacerate make your Maul and Shred attacks deal $s1% more damage and increase the critical strike chance of your Ferocious Bite ability by $s2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 34816, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


rend_and_tear_48434 = spell(
    id=48434,
    name='Rend and Tear',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=494,
    notes="druid-rework FERAL §7 (9,1), trimmed 5->3 ranks: rank 3/3 - eff0 7/14/20% Maul/Shred damage, eff1 10/20/30% Ferocious Bite crit (BP0 of the CanPrepare helper 200436), both vs the caster's own Rip or Lacerate; icon 2859 -> 494 (Ability_Druid_Disembowel) so the stock any-bleed hardcodes go inert (CORE-AUDIT row 24).",
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Targets affected by your Rip or Lacerate make your Maul and Shred attacks deal $s1% more damage and increase the critical strike chance of your Ferocious Bite ability by $s2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 34816, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


infected_wounds_48483 = spell(
    id=48483,
    name='Infected Wounds',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200427),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=2857,
    notes='druid-rework FERAL §7 (7,3): rank 1/3 - eff0 now procs Infected Wound 200427 on every rank (the 58179 attack-speed slow is cast by spell_dru_mangle instead); new eff1 +3/6/9% DOT on the feral bleeds (Rake, Lacerate, Rip, Thrash). Proc conditions come from procs_on(-48483) in druid_talents.py (10%, negative id - a positive rank row would be dropped, FERAL §10); raw ProcChance 10 only feeds $h.',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage of your feral bleeds by $s2%. Your Mangle also reduces the target's attack speed by $58179s2% for $58179d. Your Shred, Maul, Swipe and Mangle attacks have a $h% chance to cause an Infected Wound, dealing $200427o1 Nature damage plus 19% of your attack power over $200427d. Chance is modified by Proc Chance. The Infected Wound does not count as a bleed.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 10, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassSet': 7, 'EffectSpellClassMaskB_1': FERAL_BLEEDS[0], 'EffectSpellClassMaskB_2': FERAL_BLEEDS[1], 'EffectSpellClassMaskB_3': FERAL_BLEEDS[2]},
)


infected_wounds_48484 = spell(
    id=48484,
    name='Infected Wounds',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200427),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=2857,
    notes='druid-rework FERAL §7 (7,3): rank 2/3 - eff0 now procs Infected Wound 200427 on every rank (the 58180 attack-speed slow is cast by spell_dru_mangle instead); new eff1 +3/6/9% DOT on the feral bleeds (Rake, Lacerate, Rip, Thrash). Proc conditions come from procs_on(-48483) in druid_talents.py (10%, negative id - a positive rank row would be dropped, FERAL §10); raw ProcChance 10 only feeds $h.',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage of your feral bleeds by $s2%. Your Mangle also reduces the target's attack speed by $58180s2% for $58180d. Your Shred, Maul, Swipe and Mangle attacks have a $h% chance to cause an Infected Wound, dealing $200427o1 Nature damage plus 19% of your attack power over $200427d. Chance is modified by Proc Chance. The Infected Wound does not count as a bleed.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 10, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassSet': 7, 'EffectSpellClassMaskB_1': FERAL_BLEEDS[0], 'EffectSpellClassMaskB_2': FERAL_BLEEDS[1], 'EffectSpellClassMaskB_3': FERAL_BLEEDS[2]},
)


infected_wounds_48485 = spell(
    id=48485,
    name='Infected Wounds',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200427),
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=2857,
    notes='druid-rework FERAL §7 (7,3): rank 3/3 - eff0 now procs Infected Wound 200427 on every rank (the 58181 attack-speed slow is cast by spell_dru_mangle instead); new eff1 +3/6/9% DOT on the feral bleeds (Rake, Lacerate, Rip, Thrash). Proc conditions come from procs_on(-48483) in druid_talents.py (10%, negative id - a positive rank row would be dropped, FERAL §10); raw ProcChance 10 only feeds $h.',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage of your feral bleeds by $s2%. Your Mangle also reduces the target's attack speed by $58181s2% for $58181d. Your Shred, Maul, Swipe and Mangle attacks have a $h% chance to cause an Infected Wound, dealing $200427o1 Nature damage plus 19% of your attack power over $200427d. Chance is modified by Proc Chance. The Infected Wound does not count as a bleed.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 10, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassSet': 7, 'EffectSpellClassMaskB_1': FERAL_BLEEDS[0], 'EffectSpellClassMaskB_2': FERAL_BLEEDS[1], 'EffectSpellClassMaskB_3': FERAL_BLEEDS[2]},
)


gale_winds_48488 = spell(
    id=48488,
    name='Gale Winds',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COST),
    ],
    spell_icon_id=2837,
    notes='pulled from existing data; druid-rework BALANCE §6 row (8,3): eff2 moved from Cyclone range to a Hurricane mana-cost cut',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Hurricane and Typhoon by $s1%, and reduces the mana cost of Hurricane by $s2%.\n\n|cFF9D9D9DCapstone Bonus: Each time your Hurricane deals damage, the damage of your Hurricane is increased by 10% for the rest of the channel, stacking up to 5 times.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': HURRICANE, 'EffectSpellClassMaskA_2': TYPHOON, 'EffectSpellClassMaskB_1': HURRICANE, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7, 'SpellLevel': 1, 'SpellPriority': 50},
)


improved_mangle_48489 = spell(
    id=48489,
    name='Improved Mangle',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=-7, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COST),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2312,
    notes='druid-rework FERAL §7 (8,2), trimmed 3->2 ranks (48491 orphaned): rank 2/2 - eff0 Mangle (Bear) cooldown -> +10/20% damage on both Mangles (target fixed 6 -> 1); eff1 Mangle (Cat) energy -3/-6; capstone eff2 APPLY_AURA DUMMY 25 (% chance for 200435, spell_dru_mangle).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Mangle by $s1%. Reduces the energy cost of your Mangle (Cat) ability by $s2.\n\nCapstone Bonus: Your Mangle (Bear) has a $48489s3% chance to generate $/10;200435s1 rage. Your Mangle (Bear) also reduces the cooldown of Enrage by 3 sec, no more than once every 3 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': MANGLE_CAT | MANGLE_BEAR, 'EffectSpellClassMaskB_2': MANGLE_CAT, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7, 'SpellLevel': 1, 'SpellPriority': 50},
)


improved_mangle_48491 = spell(
    id=48491,
    name='Improved Mangle',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1501, implicit_target_a=6, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=-7, implicit_target_a=1, apply_aura=107, misc_value=14),
    ],
    spell_icon_id=2312,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Mangle (Bear) ability by ${$m1/-1000}.1 sec., and reduces the energy cost of your Mangle (Cat) ability by $s2.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 64, 'EffectSpellClassMaskB_2': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7, 'SpellLevel': 1, 'SpellPriority': 50},
)


king_of_the_jungle_48492 = spell(
    id=48492,
    name='King of the Jungle',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=1),
    ],
    spell_icon_id=2850,
    notes='druid-rework FERAL §7 (8,0) + §0.16 Q3: rank 1/3 - eff0 (Enrage damage 5/10/15%, BP of 51185) and eff1 (20/40/60 energy, spell_dru_tiger_s_fury_feral casts 200432 with value/10 per tick) unchanged; eff2 (form mana cost) removed on every rank - no capstone.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "While in Bear Form or Dire Bear Form, Enrage increases physical damage done by $s1%. While in Cat Form, casting Tiger's Fury restores $s2 energy over $200432d.", 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


king_of_the_jungle_48494 = spell(
    id=48494,
    name='King of the Jungle',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=1),
    ],
    spell_icon_id=2850,
    notes='druid-rework FERAL §7 (8,0) + §0.16 Q3: rank 2/3 - eff0 (Enrage damage 5/10/15%, BP of 51185) and eff1 (20/40/60 energy, spell_dru_tiger_s_fury_feral casts 200432 with value/10 per tick) unchanged; eff2 (form mana cost) removed on every rank - no capstone.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "While in Bear Form or Dire Bear Form, Enrage increases physical damage done by $s1%. While in Cat Form, casting Tiger's Fury restores $s2 energy over $200432d.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


king_of_the_jungle_48495 = spell(
    id=48495,
    name='King of the Jungle',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=59, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2850,
    notes='druid-rework FERAL §7 (8,0) + §0.16 Q3: rank 3/3 - eff0 (Enrage damage 5/10/15%, BP of 51185) and eff1 (20/40/60 energy, spell_dru_tiger_s_fury_feral casts 200432 with value/10 per tick) unchanged; eff2 (form mana cost) removed on every rank - no capstone.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "While in Bear Form or Dire Bear Form, Enrage increases physical damage done by $s1%. While in Cat Form, casting Tiger's Fury restores $s2 energy over $200432d.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


living_seed_48496 = spell(
    id=48496,
    name='Living Seed',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2860,
    notes="druid-rework RESTO §8 (7,2): eff1 stored 29->9 (live 30->10%, per rank); trigger list generalized to 'direct Nature healing spell' (Heal::IsDirectNatureHeal, via DoCheckProc added to the stock spell_dru_living_seed). Code-review fix: eff1 must stay an APPLY_AURA+DUMMY marker (Register() binds OnEffectProc to EFFECT_0/SPELL_AURA_DUMMY) - a plain SPELL_EFFECT_DUMMY effect creates no AuraEffect, so the whole passive talent never became an aura at all.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you critically heal with a direct Nature healing spell, you have a $h% chance to plant a Living Seed on the target for $s1% of the amount healed. The seed blooms when the target is next struck by a direct spell or attack. Lasts $48504d.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 33, 'ProcTypeMask': 16384, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 7},
)


living_seed_48499 = spell(
    id=48499,
    name='Living Seed',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2860,
    notes="druid-rework RESTO §8 (7,2): rank 2 of the rewrite above.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you critically heal with a direct Nature healing spell, you have a $h% chance to plant a Living Seed on the target for $s1% of the amount healed. The seed blooms when the target is next struck by a direct spell or attack. Lasts $48504d.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 66, 'ProcTypeMask': 16384, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 7},
)


living_seed_48500 = spell(
    id=48500,
    name='Living Seed',
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
    spell_icon_id=2860,
    notes="druid-rework RESTO §8 (7,2): rank 3 of the rewrite above.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you critically heal with a direct Nature healing spell, you have a $h% chance to plant a Living Seed on the target for $s1% of the amount healed. The seed blooms when the target is next struck by a direct spell or attack. Lasts $48504d.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 16384, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassSet': 7},
)


earth_and_moon_48506 = spell(
    id=48506,
    name='Earth and Moon',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL_WITH_VALUE, trigger_spell=earth_and_moon_60431.id),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=79, misc_value=72),
    ],
    spell_icon_id=2991,
    notes='pulled from existing data; druid-rework BALANCE §6 row (9,1): eff1 aura 42->231 (value overrides 60431\'s own stored amount), all three ranks trigger the same 60431 (60432/60433 orphaned - rank chain deleted); eff2 misc 126->72 (Astral); junk B_1/B_2 cleared; procs_on(-48506, ...) in druid_talents.py',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Arcane and Nature damage by $s2%. Your Wrath, Starfire, and Starsurge apply Earth and Moon, increasing magic damage taken by $60431s1% for $60431d. Does not stack with similar effects.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 7},
)


earth_and_moon_48510 = spell(
    id=48510,
    name='Earth and Moon',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL_WITH_VALUE, trigger_spell=earth_and_moon_60431.id),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=79, misc_value=72),
    ],
    spell_icon_id=2991,
    notes='pulled from existing data; druid-rework BALANCE §6 row (9,1)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Arcane and Nature damage by $s2%. Your Wrath, Starfire, and Starsurge apply Earth and Moon, increasing magic damage taken by $60431s1% for $60431d. Does not stack with similar effects.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 7},
)


earth_and_moon_48511 = spell(
    id=48511,
    name='Earth and Moon',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL_WITH_VALUE, trigger_spell=earth_and_moon_60431.id),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=79, misc_value=72),
    ],
    spell_icon_id=2991,
    notes='pulled from existing data; druid-rework BALANCE §6 row (9,1)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Arcane and Nature damage by $s2%. Your Wrath, Starfire, and Starsurge apply Earth and Moon, increasing magic damage taken by $60431s1% for $60431d. Does not stack with similar effects.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 7},
)


gale_winds_48514 = spell(
    id=48514,
    name='Gale Winds',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=-61, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COST),
    ],
    spell_icon_id=2837,
    notes='pulled from existing data; druid-rework BALANCE §6 row (8,3): final rank, carries the Hurricane-ramp capstone (200351 stack buff, spell_dru_hurricane_tick/_channel on 42231/16914, WP-B)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Hurricane and Typhoon by $s1%, and reduces the mana cost of Hurricane by $s2%.\n\nCapstone Bonus: Each time your Hurricane deals damage, the damage of your Hurricane is increased by 10% for the rest of the channel, stacking up to 5 times.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': HURRICANE, 'EffectSpellClassMaskA_2': TYPHOON, 'EffectSpellClassMaskB_1': HURRICANE, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7, 'SpellLevel': 1, 'SpellPriority': 50},
)


eclipse_48516 = spell(
    id=48516,
    name='Eclipse',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2856,
    notes='pulled from existing data; druid-rework BALANCE §6 row (8,0): rewrite of spell_dru_eclipse (stock -48516 binding kept, WP-B; BALANCE §7); eff1/eff2 are pure display values now, classmasks cleared',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Dealing damage with Starfire grants Solar Eclipse, increasing your Nature damage by $s1% for 15 sec. Dealing damage with Wrath grants Lunar Eclipse, increasing your Arcane damage by $s1% for 15 sec. Both effects cannot occur at the same time, and each can only occur once every $s2 sec.\n\n|cFF9D9D9DCapstone Bonus: The damage bonus from Eclipse is increased by your Mastery.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassMask_3': 1048576, 'SpellClassSet': 7},
)


eclipse_48521 = spell(
    id=48521,
    name='Eclipse',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2856,
    notes='pulled from existing data; druid-rework BALANCE §6 row (8,0)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Dealing damage with Starfire grants Solar Eclipse, increasing your Nature damage by $s1% for 15 sec. Dealing damage with Wrath grants Lunar Eclipse, increasing your Arcane damage by $s1% for 15 sec. Both effects cannot occur at the same time, and each can only occur once every $s2 sec.\n\n|cFF9D9D9DCapstone Bonus: The damage bonus from Eclipse is increased by your Mastery.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassMask_3': 1048576, 'SpellClassSet': 7},
)


eclipse_48525 = spell(
    id=48525,
    name='Eclipse',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2856,
    notes='pulled from existing data; druid-rework BALANCE §6 row (8,0): final rank, the Mastery gate (Druid::SPELL_ECLIPSE_R3 in DruidMechanics.h) - Mastery only applies at 3/3 Eclipse',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Dealing damage with Starfire grants Solar Eclipse, increasing your Nature damage by $s1% for 15 sec. Dealing damage with Wrath grants Lunar Eclipse, increasing your Arcane damage by $s1% for 15 sec. Both effects cannot occur at the same time, and each can only occur once every $s2 sec.\n\nCapstone Bonus: The damage bonus from Eclipse is increased by your Mastery.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassMask_3': 1048576, 'SpellClassSet': 7},
)


improved_mangle_48532 = spell(
    id=48532,
    name='Improved Mangle',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=-4, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COST),
    ],
    spell_icon_id=2312,
    notes='druid-rework FERAL §7 (8,2), trimmed 3->2 ranks (48491 orphaned): rank 1/2 - eff0 Mangle (Bear) cooldown -> +10/20% damage on both Mangles (target fixed 6 -> 1); eff1 Mangle (Cat) energy -3/-6.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Mangle by $s1%. Reduces the energy cost of your Mangle (Cat) ability by $s2.\n\n|cFF9D9D9DCapstone Bonus: Your Mangle (Bear) has a $48489s3% chance to generate $/10;200435s1 rage. Your Mangle (Bear) also reduces the cooldown of Enrage by 3 sec, no more than once every 3 sec.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': MANGLE_CAT | MANGLE_BEAR, 'EffectSpellClassMaskB_2': MANGLE_CAT, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7, 'SpellLevel': 1, 'SpellPriority': 50},
)


improved_tree_of_life_48535 = spell(
    id=48535,
    name='Improved Tree of Life',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=66, implicit_target_a=1, apply_aura=142, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=175, misc_value=4),
    ],
    spell_icon_id=2861,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your armor contribution from items while in Tree of Life Form by $s1%, and increases your healing spell power by $s2% of your spirit while in Tree of Life Form.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 1088, 'EffectSpellClassMaskB_2': 134217728, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 2, 'SpellClassSet': 7, 'SpellLevel': 1, 'SpellPriority': 50},
)


improved_tree_of_life_48536 = spell(
    id=48536,
    name='Improved Tree of Life',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=132, implicit_target_a=1, apply_aura=142, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=175, misc_value=4),
    ],
    spell_icon_id=2861,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your armor contribution from items while in Tree of Life Form by $s1%, and increases your healing spell power by $s2% of your spirit while in Tree of Life Form.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 1088, 'EffectSpellClassMaskB_2': 134217728, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 2, 'SpellClassSet': 7, 'SpellLevel': 1, 'SpellPriority': 50},
)


improved_tree_of_life_48537 = spell(
    id=48537,
    name='Improved Tree of Life',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=199, implicit_target_a=1, apply_aura=142, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=175, misc_value=4),
    ],
    spell_icon_id=2861,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your armor contribution from items while in Tree of Life Form by $s1%, and increases your healing spell power by $s2% of your spirit while in Tree of Life Form.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 1088, 'EffectSpellClassMaskB_2': 134217728, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 2, 'SpellClassSet': 7, 'SpellLevel': 1, 'SpellPriority': 50},
)


revitalize_48539 = spell(
    id=48539,
    name='Revitalize',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.OVERRIDE_CLASS_SCRIPTS),
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2862,
    notes="druid-rework RESTO §8 (8,0): eff1/eff2 are marker auras spell_dru_revitalize_resto reads (tick %/cast % respectively) - eff1 keeps stock's own OVERRIDE_CLASS_SCRIPTS aura type (Register() binds OnEffectProc to EFFECT_0/SPELL_AURA_OVERRIDE_CLASS_SCRIPTS) since a plain SPELL_EFFECT_DUMMY effect creates no AuraEffect at all (SpellEffectInfo::IsAura() requires an APPLY_AURA-family effect); eff2 is a plain DUMMY marker read via GetEffect(EFFECT_1). Rejuvenation/Wild Growth roll per tick (eff1), Healing Touch/Regrowth roll per cast (eff2). Code-review fix: both effects were SPELL_EFFECT_DUMMY, so the whole spell had zero aura effects and the passive-learn cast never created a persistent Aura at all.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your Rejuvenation and Wild Growth have a $s1% chance, and your Healing Touch and Regrowth a $s2% chance, to restore $48540s1 Energy, $/10;48541s1 Rage, $48542s1% Mana or 1% Mana to the target. Each time Revitalize triggers, you also restore 1% of your base mana.\n\n|cFF9D9D9DCapstone Bonus: Healing a target to full health with Healing Touch restores 30% of its mana cost.|r", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


revitalize_48544 = spell(
    id=48544,
    name='Revitalize',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.OVERRIDE_CLASS_SCRIPTS),
        Effect(type=EffectType.APPLY_AURA, base_points=65, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2862,
    notes='druid-rework RESTO §8 (8,0): rank 2 of the rewrite above.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your Rejuvenation and Wild Growth have a $s1% chance, and your Healing Touch and Regrowth a $s2% chance, to restore $48540s1 Energy, $/10;48541s1 Rage, $48542s1% Mana or 1% Mana to the target. Each time Revitalize triggers, you also restore 1% of your base mana.\n\n|cFF9D9D9DCapstone Bonus: Healing a target to full health with Healing Touch restores 30% of its mana cost.|r", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


revitalize_48545 = spell(
    id=48545,
    name='Revitalize',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.OVERRIDE_CLASS_SCRIPTS),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2862,
    notes='druid-rework RESTO §8 (8,0): rank 3, the final/capstone rank - new eff3 DUMMY-aura marker stored 29 (30% mana refund, cosmetic only - spell_dru_revitalize_capstone hardcodes the 30% and just checks HasAura(48545)); spell_dru_revitalize_capstone (bound to 5185) reads this rank id.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your Rejuvenation and Wild Growth have a $s1% chance, and your Healing Touch and Regrowth a $s2% chance, to restore $48540s1 Energy, $/10;48541s1 Rage, $48542s1% Mana or 1% Mana to the target. Each time Revitalize triggers, you also restore 1% of your base mana.\n\nCapstone Bonus: Healing a target to full health with Healing Touch restores 30% of its mana cost.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)
procs_on(-48539, proc_flags=PROC_FLAG_DONE_PERIODIC | PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS,
         family_name=7, family_mask=(REJUVENATION | HEALING_TOUCH | REGROWTH, WILD_GROWTH, 0),
         spell_type_mask=PROC_SPELL_TYPE_HEAL, spell_phase_mask=PROC_SPELL_PHASE_HIT, chance=100)


impurity_49220 = spell(
    id=49220,
    name='Impurity',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=3, implicit_target_a=1),
    ],
    spell_icon_id=1986,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The attack power bonus of your spells is increased by $49220s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


impurity_49633 = spell(
    id=49633,
    name='Impurity',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=7, implicit_target_a=1),
    ],
    spell_icon_id=1986,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The attack power bonus of your spells is increased by $49633s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


impurity_49635 = spell(
    id=49635,
    name='Impurity',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=11, implicit_target_a=1),
    ],
    spell_icon_id=1986,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The attack power bonus of your spells is increased by $49635s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


impurity_49636 = spell(
    id=49636,
    name='Impurity',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=15, implicit_target_a=1),
    ],
    spell_icon_id=1986,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The attack power bonus of your spells is increased by $49636s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


impurity_49638 = spell(
    id=49638,
    name='Impurity',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=19, implicit_target_a=1),
    ],
    spell_icon_id=1986,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spells receive an additional $49638s1% benefit from your attack power.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


gift_of_the_earthmother_51179 = spell(
    id=51179,
    name='Gift of the Earthmother',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL),
        Effect(type=EffectType.APPLY_AURA, base_points=-151, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.GLOBAL_COOLDOWN),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=3186,
    notes="druid-rework RESTO §8 (9,2), trimmed 5->3 ranks (51182/51183 orphaned): eff1 generalized MOD_CASTING_SPEED_NOT_STACK->HASTE_ALL; eff2 (stock GLOBAL_COOLDOWN) re-anchored to the design's 0.15/0.3/0.5 sec (stored -151/-301/-501; the live pulled value was stale); new eff3 pct DOT scoped to LIFEBLOOM (ticks only, C_2).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases spell, ranged and melee haste by $s1%. Increases the periodic healing of your Lifebloom by $s3%. Reduces the global cooldown of your Lifebloom by $/1000;s2 sec.\n\n|cFF9D9D9DCapstone Bonus: Your Lifebloom may be active on two targets at once.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 16, 'EffectSpellClassMaskA_2': 67108880, 'EffectSpellClassMaskB_2': 16, 'EffectSpellClassMaskC_2': LIFEBLOOM, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


gift_of_the_earthmother_51180 = spell(
    id=51180,
    name='Gift of the Earthmother',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL),
        Effect(type=EffectType.APPLY_AURA, base_points=-301, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.GLOBAL_COOLDOWN),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=3186,
    notes="druid-rework RESTO §8 (9,2): rank 2 of the rewrite above.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases spell, ranged and melee haste by $s1%. Increases the periodic healing of your Lifebloom by $s3%. Reduces the global cooldown of your Lifebloom by $/1000;s2 sec.\n\n|cFF9D9D9DCapstone Bonus: Your Lifebloom may be active on two targets at once.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 16, 'EffectSpellClassMaskA_2': 67108880, 'EffectSpellClassMaskB_2': 16, 'EffectSpellClassMaskC_2': LIFEBLOOM, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


gift_of_the_earthmother_51181 = spell(
    id=51181,
    name='Gift of the Earthmother',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL),
        Effect(type=EffectType.APPLY_AURA, base_points=-501, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.GLOBAL_COOLDOWN),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=3186,
    notes="druid-rework RESTO §8 (9,2): rank 3, the final/capstone rank of the rewrite above.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases spell, ranged and melee haste by $s1%. Increases the periodic healing of your Lifebloom by $s3%. Reduces the global cooldown of your Lifebloom by $/1000;s2 sec.\n\nCapstone Bonus: Your Lifebloom may be active on two targets at once.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 16, 'EffectSpellClassMaskA_2': 67108880, 'EffectSpellClassMaskB_2': 16, 'EffectSpellClassMaskC_2': LIFEBLOOM, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


gift_of_the_earthmother_51182 = spell(
    id=51182,
    name='Gift of the Earthmother',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=65, misc_value=21),
        Effect(type=EffectType.APPLY_AURA, base_points=-121, implicit_target_a=1, apply_aura=107, misc_value=21),
    ],
    spell_icon_id=3186,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total spell haste by $s1% and reduces the base cooldown of your Lifebloom spell by ${$m2/-15}%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 16, 'EffectSpellClassMaskA_2': 67108880, 'EffectSpellClassMaskB_2': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


gift_of_the_earthmother_51183 = spell(
    id=51183,
    name='Gift of the Earthmother',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=65, misc_value=21),
        Effect(type=EffectType.APPLY_AURA, base_points=-151, implicit_target_a=1, apply_aura=107, misc_value=21),
    ],
    spell_icon_id=3186,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total spell haste by $s1% and reduces the base cooldown of your Lifebloom spell by ${$m2/-15}%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 16, 'EffectSpellClassMaskA_2': 67108880, 'EffectSpellClassMaskB_2': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


rend_and_tear_51268 = spell(
    id=51268,
    name='Rend and Tear',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=494,
    notes='druid-rework FERAL §1: orphaned old Rend and Tear rank (talent trimmed 5->3), kept declared; icon 2859 -> 494 like the live ranks so no DUMMY aura stays on the retired icon (CORE-AUDIT §4).',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases damage done by your Maul and Shred attacks on bleeding targets by $s1%, and increases the critical strike chance of your Ferocious Bite ability on bleeding targets by $s2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 34816, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


rend_and_tear_51269 = spell(
    id=51269,
    name='Rend and Tear',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=494,
    notes='druid-rework FERAL §1: orphaned old Rend and Tear rank (talent trimmed 5->3), kept declared; icon 2859 -> 494 like the live ranks so no DUMMY aura stays on the retired icon (CORE-AUDIT §4).',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases damage done by your Maul and Shred attacks on bleeding targets by $s1%, and increases the critical strike chance of your Ferocious Bite ability on bleeding targets by $s2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 34816, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


genesis_57810 = spell(
    id=57810,
    name='Genesis',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=1957,
    notes='pulled from existing data; druid-rework BALANCE §6 row (0,2): trimmed 5->3 ranks, uniform masks on every rank (stock rank 2 had a stray classmask), GENESIS_DOT/GENESIS_TICKS composites from _masks.py (PLAN §0.10 already folds in Cenarion Ward/Cultivation)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the periodic damage and healing of your Druid spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': GENESIS_DOT[0], 'EffectSpellClassMaskA_2': GENESIS_DOT[1], 'EffectSpellClassMaskA_3': GENESIS_DOT[2], 'EffectSpellClassMaskB_1': GENESIS_TICKS[0], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


genesis_57811 = spell(
    id=57811,
    name='Genesis',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=1957,
    notes='pulled from existing data; druid-rework BALANCE §6 row (0,2)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the periodic damage and healing of your Druid spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': GENESIS_DOT[0], 'EffectSpellClassMaskA_2': GENESIS_DOT[1], 'EffectSpellClassMaskA_3': GENESIS_DOT[2], 'EffectSpellClassMaskB_1': GENESIS_TICKS[0], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


genesis_57812 = spell(
    id=57812,
    name='Genesis',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=1957,
    notes='pulled from existing data; druid-rework BALANCE §6 row (0,2)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the periodic damage and healing of your Druid spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': GENESIS_DOT[0], 'EffectSpellClassMaskA_2': GENESIS_DOT[1], 'EffectSpellClassMaskA_3': GENESIS_DOT[2], 'EffectSpellClassMaskB_1': GENESIS_TICKS[0], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


genesis_57813 = spell(
    id=57813,
    name='Genesis',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=1957,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage and healing done by your periodic spell damage and healing effects by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2097746, 'EffectSpellClassMaskA_2': 67108880, 'EffectSpellClassMaskB_1': 4194432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


genesis_57814 = spell(
    id=57814,
    name='Genesis',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=1957,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage and healing done by your periodic spell damage and healing effects by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2097746, 'EffectSpellClassMaskA_2': 67108880, 'EffectSpellClassMaskB_1': 4194432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


improved_insect_swarm_57849 = spell(
    id=57849,
    name='Improved Insect Swarm',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=116,
    notes='pulled from existing data; druid-rework BALANCE §6 row (4,2)/§0.2 correction: eff1 moved off DUMMY (CORE-AUDIT row 3/4 inert-key retirement, icon 1771->1790); eff2 stays a plain DUMMY percent read directly by Druid::ApplyDoneDamagePctMods (no bucket function - PLAN §0.2)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Insect Swarm by $s1%. Your Wrath deals $s2% increased damage to targets afflicted by your Insect Swarm, and your Starfire deals $s2% increased damage to targets afflicted by your Moonfire.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': INSECT_SWARM, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


improved_insect_swarm_57850 = spell(
    id=57850,
    name='Improved Insect Swarm',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=116,
    notes='pulled from existing data; druid-rework BALANCE §6 row (4,2)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Insect Swarm by $s1%. Your Wrath deals $s2% increased damage to targets afflicted by your Insect Swarm, and your Starfire deals $s2% increased damage to targets afflicted by your Moonfire.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': INSECT_SWARM, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


improved_insect_swarm_57851 = spell(
    id=57851,
    name='Improved Insect Swarm',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=116,
    notes='pulled from existing data; druid-rework BALANCE §6 row (4,2)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Insect Swarm by $s1%. Your Wrath deals $s2% increased damage to targets afflicted by your Insect Swarm, and your Starfire deals $s2% increased damage to targets afflicted by your Moonfire.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': INSECT_SWARM, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


nature_s_splendor_57865 = spell(
    id=57865,
    name="Nature's Splendor",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2999, implicit_target_a=1, apply_aura=107, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=5999, implicit_target_a=1, apply_aura=107, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=1999, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=2013,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the duration of your Moonfire and Rejuvenation spells by ${$m1/1000} sec, your Regrowth spell by ${$m2/1000} sec, and your Insect Swarm and Lifebloom spells by ${$m3/1000} sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 18, 'EffectSpellClassMaskB_1': 64, 'EffectSpellClassMaskC_1': 2097152, 'EffectSpellClassMaskC_2': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


protector_of_the_pack_57873 = spell(
    id=57873,
    name='Protector of the Pack',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_ATTACK_POWER_PCT, misc_value=23),
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.EFFECT1),
    ],
    spell_icon_id=957,
    notes='druid-rework FERAL §7 (7,0): rank 1/3 - eff0 AP% unchanged; eff1 damage taken all schools -> physical only, -2/-4/-6% (spell_dru_protector_of_the_pack zeroes it in Bestial Fury); new eff2 +7/14/20% Demoralizing Roar EFFECT1 (the AP reduction). Stock bear ShapeshiftMask kept (WP-BRIEF §3).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While in Bear Form or Dire Bear Form your attack power is increased by $s1% and the physical damage you take is reduced by $s2%. Increases the melee attack power reduction of your Demoralizing Roar by $s3%. The damage reduction is suppressed while Bestial Fury is active.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': SS_ANY_BEAR, 'SpellClassSet': 7, 'EffectSpellClassMaskC_1': DEMORALIZING_ROAR},
)


protector_of_the_pack_57876 = spell(
    id=57876,
    name='Protector of the Pack',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.MOD_ATTACK_POWER_PCT, misc_value=23),
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=13, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.EFFECT1),
    ],
    spell_icon_id=957,
    notes='druid-rework FERAL §7 (7,0): rank 2/3 - eff0 AP% unchanged; eff1 damage taken all schools -> physical only, -2/-4/-6% (spell_dru_protector_of_the_pack zeroes it in Bestial Fury); new eff2 +7/14/20% Demoralizing Roar EFFECT1 (the AP reduction). Stock bear ShapeshiftMask kept (WP-BRIEF §3).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While in Bear Form or Dire Bear Form your attack power is increased by $s1% and the physical damage you take is reduced by $s2%. Increases the melee attack power reduction of your Demoralizing Roar by $s3%. The damage reduction is suppressed while Bestial Fury is active.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': SS_ANY_BEAR, 'SpellClassSet': 7, 'EffectSpellClassMaskC_1': DEMORALIZING_ROAR},
)


protector_of_the_pack_57877 = spell(
    id=57877,
    name='Protector of the Pack',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.MOD_ATTACK_POWER_PCT, misc_value=23),
        Effect(type=EffectType.APPLY_AURA, base_points=-7, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.EFFECT1),
    ],
    spell_icon_id=957,
    notes='druid-rework FERAL §7 (7,0): rank 3/3 - eff0 AP% unchanged; eff1 damage taken all schools -> physical only, -2/-4/-6% (spell_dru_protector_of_the_pack zeroes it in Bestial Fury); new eff2 +7/14/20% Demoralizing Roar EFFECT1 (the AP reduction). Stock bear ShapeshiftMask kept (WP-BRIEF §3).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While in Bear Form or Dire Bear Form your attack power is increased by $s1% and the physical damage you take is reduced by $s2%. Increases the melee attack power reduction of your Demoralizing Roar by $s3%. The damage reduction is suppressed while Bestial Fury is active.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': SS_ANY_BEAR, 'SpellClassSet': 7, 'EffectSpellClassMaskC_1': DEMORALIZING_ROAR},
)


natural_reaction_57878 = spell(
    id=57878,
    name='Natural Reaction',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.MOD_RATING_FROM_STAT, misc_value=1 << CombatRating.DODGE),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=57893),
    ],
    spell_icon_id=50,
    notes='druid-rework FERAL §7 (5,0): rank 1/3 - eff0 dodge % aura -> MOD_RATING_FROM_STAT dodge rating from Agility 5/10/15% (misc 1<<CR_DODGE, MiscValueB 1 = STAT_AGILITY); eff1 proc to 57893 kept (retuned to 5/10/15 rage); stock spell_proc -57878 (dodge) kept.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your dodge rating by $s1% of your Agility while in Bear Form or Dire Bear Form. You regenerate $/10;57893s1 rage every time you dodge while in Bear Form or Dire Bear Form.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 172712, 'RangeIndex': 1, 'ShapeshiftMask': SS_ANY_BEAR, 'SpellClassSet': 7, 'EffectMiscValueB_1': 1},
)


natural_reaction_57880 = spell(
    id=57880,
    name='Natural Reaction',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.MOD_RATING_FROM_STAT, misc_value=1 << CombatRating.DODGE),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=59071),
    ],
    spell_icon_id=50,
    notes='druid-rework FERAL §7 (5,0): rank 2/3 - eff0 dodge % aura -> MOD_RATING_FROM_STAT dodge rating from Agility 5/10/15% (misc 1<<CR_DODGE, MiscValueB 1 = STAT_AGILITY); eff1 proc to 59071 kept (retuned to 5/10/15 rage); stock spell_proc -57878 (dodge) kept.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your dodge rating by $s1% of your Agility while in Bear Form or Dire Bear Form. You regenerate $/10;59071s1 rage every time you dodge while in Bear Form or Dire Bear Form.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 10920, 'RangeIndex': 1, 'ShapeshiftMask': SS_ANY_BEAR, 'SpellClassSet': 7, 'EffectMiscValueB_1': 1},
)


natural_reaction_57881 = spell(
    id=57881,
    name='Natural Reaction',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.MOD_RATING_FROM_STAT, misc_value=1 << CombatRating.DODGE),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=59072),
    ],
    spell_icon_id=50,
    notes='druid-rework FERAL §7 (5,0): rank 3/3 - eff0 dodge % aura -> MOD_RATING_FROM_STAT dodge rating from Agility 5/10/15% (misc 1<<CR_DODGE, MiscValueB 1 = STAT_AGILITY); eff1 proc to 59072 kept (retuned to 5/10/15 rage); stock spell_proc -57878 (dodge) kept.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your dodge rating by $s1% of your Agility while in Bear Form or Dire Bear Form. You regenerate $/10;59072s1 rage every time you dodge while in Bear Form or Dire Bear Form.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 10920, 'RangeIndex': 1, 'ShapeshiftMask': SS_ANY_BEAR, 'SpellClassSet': 7, 'EffectMiscValueB_1': 1},
)


nature_s_grace_61345 = spell(
    id=61345,
    name="Nature's Grace",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL_WITH_VALUE, trigger_spell=16886),
    ],
    spell_icon_id=10,
    notes='pulled from existing data; druid-rework BALANCE §6 row (2,0)',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your direct damage and healing Druid spell critical strikes have a $h% chance to grant Nature\'s Grace, increasing spell, ranged, and melee haste by $16886s1% for $16886d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 66, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 7},
)


nature_s_grace_61346 = spell(
    id=61346,
    name="Nature's Grace",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=20, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL_WITH_VALUE, trigger_spell=16886),
    ],
    spell_icon_id=10,
    notes='pulled from existing data; druid-rework BALANCE §6 row (2,0): final rank',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your direct damage and healing Druid spell critical strikes have a $h% chance to grant Nature\'s Grace, increasing spell, ranged, and melee haste by $16886s1% for $16886d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 7},
)


improved_barkskin_63410 = spell(
    id=63410,
    name='Improved Barkskin',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-6, implicit_target_a=1, apply_aura=107, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=79, implicit_target_a=1, apply_aura=107, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=34, implicit_target_a=1, apply_aura=107, misc_value=28),
    ],
    spell_icon_id=689,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Grants $s2% additional armor contribution from cloth and leather items while in Travel Form or while not shapeshifted, increases the damage reduction granted by your Barkskin spell by $s1% and reduces the chance your Barkskin is dispelled by $s3%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 262144, 'EffectSpellClassMaskB_3': 131072, 'EffectSpellClassMaskC_2': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


improved_barkskin_63411 = spell(
    id=63411,
    name='Improved Barkskin',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=107, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=159, implicit_target_a=1, apply_aura=107, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=69, implicit_target_a=1, apply_aura=107, misc_value=28),
    ],
    spell_icon_id=689,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Grants $s2% additional armor contribution from cloth and leather items while in Travel Form or while not shapeshifted, increases the damage reduction granted by your Barkskin spell by $s1% and reduces the chance your Barkskin is dispelled by $s3%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 262144, 'EffectSpellClassMaskB_3': 131072, 'EffectSpellClassMaskC_2': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


primal_gore_63503 = spell(
    id=63503,
    name='Primal Gore',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.CRIT_DAMAGE_BONUS),
    ],
    spell_icon_id=262,
    notes="druid-rework FERAL §7 (9,2) + CORE-AUDIT row 25 (C2): rank 1/3 - aura 286 -> ADD_PCT_MODIFIER CRIT_DAMAGE_BONUS +30% of the crit's extra damage on the feral bleeds (Rake, Lacerate, Rip, Thrash) = x1.15 of a 200% crit.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage of your bleeds by ${$m1/2}%.\n\n|cFF9D9D9DCapstone Bonus: While in Cat Form, your bleed damage is increased by $200471s2% of your Mastery.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': FERAL_BLEEDS[0], 'EffectSpellClassMaskA_2': FERAL_BLEEDS[1], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7, 'EffectSpellClassMaskA_3': FERAL_BLEEDS[2]},
)


# --- druid-rework Balance WP-0 pull list (druid-rework.BALANCE.md §3 item 1, §0.11) ---
# Pulled via pull_dsl.py so the Balance pass can edit these rows; their legacy source/spells/npc.csv
# rows are deleted in this same change (generate.py rejects an id declared in both places).

owlkin_frenzy_48391 = spell(
    id=48391,
    name='Owlkin Frenzy',
    school=School.NORMAL,
    dispel=9,
    mechanic=31,
    attributes=134479872,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=72),
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.PERIODIC_ENERGIZE, amplitude=2000),
    ],
    spell_icon_id=2853,
    notes='pulled from existing data; druid-rework BALANCE §6 row (7,0): eff1 moved from a pushback-immunity SpellMod to a display-value MOD_DAMAGE_PERCENT_DONE/Astral bucket aura (BP0 overridden by the 231 trigger on 48389/48392/48393); eff2 (old misc 127 damage%) dropped; eff3 (energize, EFFECT_2 in spell_dru_owlkin_frenzy) untouched',
    raw_overrides={'AttributesEx': 32768, 'AttributesEx3': 262144, 'ShapeshiftMask': 1073741824, 'CastingTimeIndex': 1, 'ProcChance': 101, 'SpellLevel': 1, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 11720, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'While in Moonkin Form, your direct Arcane and Nature damage spells have a 10% chance to trigger Owlkin Frenzy, and melee hits against you have a 30% chance. Owlkin Frenzy increases your Arcane and Nature damage by $s1% for $d, and restores $s3% of base mana every $t3 sec.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Arcane and Nature damage increased by $s1%. $s3% of base mana is restored every $t3 sec.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 7, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


eclipse_solar_48517 = spell(
    id=48517,
    name='Solar Eclipse',
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3449,
    notes='pulled from existing data; druid-rework BALANCE §6 row (8,0)/§7: DUMMY display buff, BP0 overridden by spell_dru_eclipse\'s HandleProc (WP-B); classmask cleared',
    raw_overrides={'AttributesEx6': 64, 'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 12705, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'Nature damage increased by $s1%.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Nature damage increased by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 7, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


eclipse_lunar_48518 = spell(
    id=48518,
    name='Lunar Eclipse',
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2856,
    notes='pulled from existing data; druid-rework BALANCE §6 row (8,0)/§7',
    raw_overrides={'AttributesEx6': 64, 'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 11567, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'Arcane damage increased by $s1%.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Arcane damage increased by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 7, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


nature_s_grace_16886 = spell(
    id=16886,
    name="Nature's Grace",
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=4000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL, misc_value=0),
    ],
    spell_icon_id=10,
    notes='pulled from existing data; druid-rework BALANCE §6 row (2,0): eff1 aura 65->193 (HASTE_ALL, display value - BP0 overridden by the procs_on(-16880) trigger); duration 3s->4s; stale classmasks cleared',
    raw_overrides={'AttributesEx4': 64, 'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': "Your direct damage and healing Druid spell critical strikes have a $h% chance to grant Nature's Grace, increasing spell, ranged, and melee haste by $16886s1% for $16886d.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Spell, ranged, and melee haste increased by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 7, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


moonkin_form_passive_24905 = spell(
    id=24905,
    name='Moonkin Form (Passive)',
    school=School.NATURE,
    attributes=80,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=142, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=53506),
    ],
    spell_icon_id=111,
    notes='pulled from existing data; druid-rework BALANCE §6 row (6,1): eff1 40% armor (was ~370% - the stock rank\'s single-rank bootstrap value); eff3 (53506, 2% mana proc) unchanged, gated by procs_on(24905, ...) in druid_talents.py + Druid::IsDirectDamageCast (spell_dru_moonkin_form_passive_proc rewrite, WP-B)',
    raw_overrides={'AttributesEx3': 67108864, 'ShapeshiftMask': 1073741824, 'CastingTimeIndex': 1, 'ProcTypeMask': 70656, 'ProcChance': 100, 'MaxLevel': 70, 'BaseLevel': 40, 'SpellLevel': 40, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Passive', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712188, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 7, 'SpellClassMask_3': 4, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


moonkin_form_passive_69366 = spell(
    id=69366,
    name='Moonkin Form (Passive)',
    school=School.NATURE,
    attributes=336,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=111,
    notes='pulled from existing data; druid-rework BALANCE §6 row (6,1)/CORE-AUDIT row 10: the stun-absorb SCHOOL_ABSORB effect made a permanently inert DUMMY; unbind_script(69366, \'spell_dru_moonkin_form_passive\') in druid_talents.py stops the stock class casting it (SpellAuraEffects.cpp:1399 still casts this spell id on Moonkin entry, but it now does nothing)',
    raw_overrides={'ShapeshiftMask': 1073741824, 'CastingTimeIndex': 1, 'ProcChance': 101, 'MaxLevel': 70, 'BaseLevel': 40, 'SpellLevel': 40, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Passive', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712188, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 7, 'SpellClassMask_3': 4, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


# --- druid-rework Balance WP-A: new talent-rank passives (BALANCE.md §2/§6) ---

celestial_attunement_200320 = spell(
    id=200320,
    name='Celestial Attunement',
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
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL, misc_value=0),
    ],
    spell_icon_id=1952,
    notes='NEW (druid-rework BALANCE §6 row 0,0; talent 1785 repurposed from Improved Faerie Fire)',
    raw_overrides={'SpellClassSet': 7, 'ProcChance': 101, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell, ranged, and melee haste by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Spell, ranged, and melee haste increased by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


celestial_attunement_200321 = spell(
    id=200321,
    name='Celestial Attunement',
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
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL, misc_value=0),
    ],
    spell_icon_id=1952,
    notes='NEW (druid-rework BALANCE §6 row 0,0)',
    raw_overrides={'SpellClassSet': 7, 'ProcChance': 101, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell, ranged, and melee haste by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Spell, ranged, and melee haste increased by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


celestial_attunement_200322 = spell(
    id=200322,
    name='Celestial Attunement',
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
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL, misc_value=0),
    ],
    spell_icon_id=1952,
    notes='NEW (druid-rework BALANCE §6 row 0,0)',
    raw_overrides={'SpellClassSet': 7, 'ProcChance': 101, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell, ranged, and melee haste by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Spell, ranged, and melee haste increased by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


improved_moonfire_200323 = spell(
    id=200323,
    name='Improved Moonfire',
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
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=71, misc_value=64),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=225,
    notes='NEW rank 3 (druid-rework BALANCE §6 row 1,2 - clone of 16822 with rank-3 values); carries the capstone proc (procs_on(200323, ...) in druid_talents.py, spell_dru_improved_moonfire_capstone casts 200341 Lunar Flare, WP-B)',
    raw_overrides={'SpellClassSet': 7, 'ProcChance': 101, 'EquippedItemClass': -1, 'EffectSpellClassMaskB_1': 2, 'EffectSpellClassMaskC_1': 2, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Moonfire by $s2% and the critical strike chance of your Arcane spells by $s1%.\n\nCapstone Bonus: Your direct Arcane critical strikes on targets afflicted by your Moonfire trigger an extra $200341s1 Arcane damage. This can occur once every 1.5 sec.', 'AuraDescription_Lang_Mask': 16712188, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


lunar_flare_200341 = spell(
    id=200341,
    name='Lunar Flare',
    school=School.ARCANE,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=18.3, potency_kind='direct', implicit_target_a=6),
    ],
    spell_icon_id=225,
    notes='NEW (druid-rework BALANCE §6 row 1,2 capstone hit): scales with level (PLAN B3), learn level 15 (Improved Moonfire\'s tier), level-60 value 50 -> ppl 50/60; cast by spell_dru_improved_moonfire_capstone (WP-B). Potency system P5 (druid pass): converted to sp_potency=18.3 (potency-report default, base/coef already agreed); the old bonus_coefficients(direct=0.1) spell_bonus_data override is retired in favor of the generated DBC coefficient.',
    raw_overrides={'BaseLevel': 15, 'SpellLevel': 15, 'MaxLevel': 80, 'DefenseType': 1, 'SpellClassSet': 7, 'ProcChance': 101, 'AttributesEx2': 536870912, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes {pot1} Arcane damage to the target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


nature_s_splendor_200324 = spell(
    id=200324,
    name="Nature's Splendor",
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
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=108, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=108, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=2013,
    notes='NEW (druid-rework BALANCE §6 row 2,2 - talent 2240\'s own rank ids; stock 57865 stays unchanged and becomes the r3-linked capstone aura, linked_spell(200326, 57865, type=2) in druid_talents.py)',
    raw_overrides={'SpellClassSet': 7, 'ProcChance': 101, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 66, 'EffectSpellClassMaskB_1': 2097234, 'EffectSpellClassMaskB_2': LIFEBLOOM, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the healing of your Rejuvenation, Regrowth, and Lifebloom by $s1%, and the damage of your Moonfire and Insect Swarm by $s2%.\n\n|cFF9D9D9DCapstone Bonus: Increases the duration of your Moonfire and Rejuvenation by 3 sec, your Regrowth by 6 sec, and your Insect Swarm and Lifebloom by 2 sec.|r', 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


nature_s_splendor_200325 = spell(
    id=200325,
    name="Nature's Splendor",
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
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=108, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=108, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=2013,
    notes='NEW (druid-rework BALANCE §6 row 2,2)',
    raw_overrides={'SpellClassSet': 7, 'ProcChance': 101, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 66, 'EffectSpellClassMaskB_1': 2097234, 'EffectSpellClassMaskB_2': LIFEBLOOM, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the healing of your Rejuvenation, Regrowth, and Lifebloom by $s1%, and the damage of your Moonfire and Insect Swarm by $s2%.\n\n|cFF9D9D9DCapstone Bonus: Increases the duration of your Moonfire and Rejuvenation by 3 sec, your Regrowth by 6 sec, and your Insect Swarm and Lifebloom by 2 sec.|r', 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


nature_s_splendor_200326 = spell(
    id=200326,
    name="Nature's Splendor",
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
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=108, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=108, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=2013,
    notes='NEW (druid-rework BALANCE §6 row 2,2): final rank, linked to stock 57865 (linked_spell(200326, 57865, type=2) in druid_talents.py) for the capstone durations',
    raw_overrides={'SpellClassSet': 7, 'ProcChance': 101, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 66, 'EffectSpellClassMaskB_1': 2097234, 'EffectSpellClassMaskB_2': LIFEBLOOM, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the healing of your Rejuvenation, Regrowth, and Lifebloom by $s1%, and the damage of your Moonfire and Insect Swarm by $s2%.\n\nCapstone Bonus: Increases the duration of your Moonfire and Rejuvenation by 3 sec, your Regrowth by 6 sec, and your Insect Swarm and Lifebloom by 2 sec.', 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


starweaver_200327 = spell(
    id=200327,
    name='Starweaver',
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
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=-1001, implicit_target_a=1, apply_aura=107, misc_value=SpellModOp.COOLDOWN),
    ],
    spell_icon_id=1954,
    notes='NEW (druid-rework BALANCE §6 row 3,0; talent 60026 minted)',
    raw_overrides={'SpellClassSet': 7, 'ProcChance': 101, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_2': STARFALL, 'EffectSpellClassMaskA_3': STARSURGE, 'EffectSpellClassMaskB_3': STARSURGE, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by Starsurge and Starfall by $s1%. Reduces the cooldown of Starsurge by $/1000;s2 sec.\n\n|cFF9D9D9DCapstone Bonus: Casting Starsurge lowers the remaining cooldown of Starfall by 2 sec.|r', 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


starweaver_200328 = spell(
    id=200328,
    name='Starweaver',
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
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=-2001, implicit_target_a=1, apply_aura=107, misc_value=SpellModOp.COOLDOWN),
    ],
    spell_icon_id=1954,
    notes='NEW (druid-rework BALANCE §6 row 3,0)',
    raw_overrides={'SpellClassSet': 7, 'ProcChance': 101, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_2': STARFALL, 'EffectSpellClassMaskA_3': STARSURGE, 'EffectSpellClassMaskB_3': STARSURGE, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by Starsurge and Starfall by $s1%. Reduces the cooldown of Starsurge by $/1000;s2 sec.\n\n|cFF9D9D9DCapstone Bonus: Casting Starsurge lowers the remaining cooldown of Starfall by 2 sec.|r', 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


starweaver_200329 = spell(
    id=200329,
    name='Starweaver',
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
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=-3001, implicit_target_a=1, apply_aura=107, misc_value=SpellModOp.COOLDOWN),
    ],
    spell_icon_id=1954,
    notes='NEW (druid-rework BALANCE §6 row 3,0): final rank, carries the capstone (spell_dru_starsurge AfterCast checks HasAura(200329) -> Druid::ReduceSpellCooldown(48505, 2000), WP-B)',
    raw_overrides={'SpellClassSet': 7, 'ProcChance': 101, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_2': STARFALL, 'EffectSpellClassMaskA_3': STARSURGE, 'EffectSpellClassMaskB_3': STARSURGE, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by Starsurge and Starfall by $s1%. Reduces the cooldown of Starsurge by $/1000;s2 sec.\n\nCapstone Bonus: Casting Starsurge lowers the remaining cooldown of Starfall by 2 sec.', 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


swarming_rot_200330 = spell(
    id=200330,
    name='Swarming Rot',
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
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=108, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=1468,
    notes='NEW (druid-rework BALANCE §6 row 3,1; talent 60027 minted)',
    raw_overrides={'SpellClassSet': 7, 'ProcChance': 101, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': INSECT_SWARM, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Insect Swarm by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Each time your Insect Swarm deals damage, it also applies Insect Swarm to one enemy within 8 yards that is already in combat with you and not already afflicted. Copies do not spread further.|r', 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


swarming_rot_200331 = spell(
    id=200331,
    name='Swarming Rot',
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
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=1468,
    notes='NEW (druid-rework BALANCE §6 row 3,1)',
    raw_overrides={'SpellClassSet': 7, 'ProcChance': 101, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': INSECT_SWARM, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Insect Swarm by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Each time your Insect Swarm deals damage, it also applies Insect Swarm to one enemy within 8 yards that is already in combat with you and not already afflicted. Copies do not spread further.|r', 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


swarming_rot_200332 = spell(
    id=200332,
    name='Swarming Rot',
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
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=1468,
    notes='NEW (druid-rework BALANCE §6 row 3,1): final rank, carries the propagation capstone (procs_on(200332, ...) in druid_talents.py, spell_dru_swarming_rot casts 200352 on original-5570 ticks only, WP-B)',
    raw_overrides={'SpellClassSet': 7, 'ProcChance': 101, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': INSECT_SWARM, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Insect Swarm by $s1%.\n\nCapstone Bonus: Each time your Insect Swarm deals damage, it also applies Insect Swarm to one enemy within 8 yards that is already in combat with you and not already afflicted. Copies do not spread further.', 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


insect_swarm_200352 = spell(
    id=200352,
    name='Insect Swarm',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,  # script-cast on a unit: RangeIndex 0 = 0yd, fails CheckRange
    duration_ms=14000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, sp_potency=34.8, potency_kind='periodic', implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=2000),
    ],
    spell_icon_id=1771,
    notes="NEW (druid-rework BALANCE §6 row 3,1 capstone copy): clone of 5570's eff1 only (same base/ppl/coefficient), shares Insect Swarm's family bit (INSECT_SWARM), no script binding - propagation is linear only (spell_dru_swarming_rot never re-triggers off a copy). Potency system P5 (druid pass): converted to sp_potency=34.8, same as 5570 (not mismatched; potency-report base-damage default).",
    raw_overrides={'BaseLevel': 20, 'SpellLevel': 20, 'MaxLevel': 80, 'DefenseType': 1, 'SpellClassSet': 7, 'ProcChance': 101, 'SpellClassMask_1': INSECT_SWARM, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The enemy target is swarmed by insects, causing {pot1.total} Nature damage over $d.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '{pot1} Nature damage every $t1 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


brambles_silence_200353 = spell(
    id=200353,
    name='Brambles',
    school=School.NATURE,
    mechanic=Mechanic.SILENCE,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    duration_ms=4000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, mechanic=Mechanic.SILENCE, implicit_target_a=6, apply_aura=27),
    ],
    spell_icon_id=53,
    notes='NEW (druid-rework BALANCE §6 row 4,3 capstone): cast by spell_dru_brambles_silence (AuraScript on 16840, WP-B) whenever the caster\'s Entangling Roots takes effect; range_yards 100 (not 0): Spell::CheckRange runs even for triggered casts, and RangeIndex 0 means max range 0 so the silence failed OUT_OF_RANGE beyond melee',
    raw_overrides={'DefenseType': 1, 'PreventionType': 2, 'SpellClassSet': 7, 'ProcChance': 101, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Silenced.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Silenced.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


shooting_stars_200342 = spell(
    id=200342,
    name='Shooting Stars',
    school=School.NORMAL,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=107, misc_value=SpellModOp.CRITICAL_CHANCE),
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=108, misc_value=SpellModOp.COOLDOWN),
    ],
    spell_icon_id=1485,
    notes='NEW (druid-rework BALANCE §6 row 3,2 capstone buff): 1 charge, no spell_proc row (Player::RemoveSpellMods only drops charges when one exists); cast by procs_on(16923, ...)\'s AuraScript (WP-B) - Moonfire/Insect Swarm ticks empower the next Starsurge',
    raw_overrides={'ProcCharges': 1, 'ProcTypeMask': 0, 'SpellClassSet': 7, 'ProcChance': 101, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_3': STARSURGE, 'EffectSpellClassMaskB_3': STARSURGE, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your next Starsurge does not trigger its cooldown and is a guaranteed critical strike.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next Starsurge does not trigger its cooldown and is a guaranteed critical strike.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


vengeful_soul_200343 = spell(
    id=200343,
    name='Vengeful Soul',
    school=School.NORMAL,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=126),
    ],
    spell_icon_id=1987,
    notes='NEW (druid-rework BALANCE §6 row 6,3 capstone buff): a bucket aura (PLAN §0.2, ordinary MOD_DAMAGE_PERCENT_DONE multiplier for druid casters); cast by procs_on(16911, ...)\'s AuraScript, energizes 10% of missing mana on expiry (spell_dru_vengeful_soul, WP-B)',
    raw_overrides={'SpellClassSet': 7, 'ProcChance': 101, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Magic damage increased by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Magic damage increased by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


astral_surge_200344 = spell(
    id=200344,
    name='Astral Surge',
    school=School.NORMAL,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_DONE, misc_value=72),
    ],
    spell_icon_id=1961,
    notes='NEW (druid-rework BALANCE §6 row 5,1 capstone, slot 1/3): CORE-AUDIT row 6 (PLAN C1 accepted) - flat SP worth 10% of the caster\'s current Arcane/Nature spell power, computed once when cast by spell_dru_astral_surge_sp\'s DoEffectCalcAmount (WP-B); base_points here is a display placeholder only, overridden by SetAmount',
    raw_overrides={'SpellClassSet': 7, 'ProcChance': 101, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell power for Arcane and Nature damage by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Spell power for Arcane and Nature damage increased.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


astral_surge_200345 = spell(
    id=200345,
    name='Astral Surge',
    school=School.NORMAL,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_DONE, misc_value=72),
    ],
    spell_icon_id=1961,
    notes='NEW (druid-rework BALANCE §6 row 5,1 capstone, slot 2/3)',
    raw_overrides={'SpellClassSet': 7, 'ProcChance': 101, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell power for Arcane and Nature damage by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Spell power for Arcane and Nature damage increased.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


astral_surge_200346 = spell(
    id=200346,
    name='Astral Surge',
    school=School.NORMAL,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_DONE, misc_value=72),
    ],
    spell_icon_id=1961,
    notes='NEW (druid-rework BALANCE §6 row 5,1 capstone, slot 3/3)',
    raw_overrides={'SpellClassSet': 7, 'ProcChance': 101, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell power for Arcane and Nature damage by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Spell power for Arcane and Nature damage increased.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


balance_of_power_buff_200347 = spell(
    id=200347,
    name='Balance of Power',
    school=School.NORMAL,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_DONE, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.MOD_HEALING_DONE, misc_value=126),
    ],
    spell_icon_id=2247,
    notes='NEW (druid-rework BALANCE §6 row 5,2 buff): CORE-AUDIT row 6 (PLAN C1 accepted) - flat SP/heal worth BP0% of current spell power, computed once when cast by spell_dru_eclipse\'s HandleProc / spell_dru_astral_surge_sp (WP-B); BP0 overrides both effects\' stored amounts',
    raw_overrides={'SpellClassSet': 7, 'ProcChance': 101, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell power by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Spell power increased by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


moonglow_buff_200348 = spell(
    id=200348,
    name='Moonglow',
    school=School.NORMAL,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=4),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=AuraType.MOD_MANA_REGEN_INTERRUPT),
    ],
    spell_icon_id=310,
    notes='NEW (druid-rework BALANCE §6 row 1,0 capstone buff, rank 1/3): joins A7\'s spell_group (max-not-sum with Intensity, PLAN §6.7) - group id declared in druid_talents.py',
    raw_overrides={'SpellClassSet': 7, 'ProcChance': 101, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Spirit increased by $s1% and mana regeneration while casting increased by $s2%.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Spirit increased by $s1% and mana regeneration while casting increased by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


moonglow_buff_200349 = spell(
    id=200349,
    name='Moonglow',
    school=School.NORMAL,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=4),
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=AuraType.MOD_MANA_REGEN_INTERRUPT),
    ],
    spell_icon_id=310,
    notes='NEW (druid-rework BALANCE §6 row 1,0 capstone buff, rank 2/3)',
    raw_overrides={'SpellClassSet': 7, 'ProcChance': 101, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Spirit increased by $s1% and mana regeneration while casting increased by $s2%.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Spirit increased by $s1% and mana regeneration while casting increased by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


moonglow_buff_200350 = spell(
    id=200350,
    name='Moonglow',
    school=School.NORMAL,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=4),
        Effect(type=EffectType.APPLY_AURA, base_points=74, implicit_target_a=1, apply_aura=AuraType.MOD_MANA_REGEN_INTERRUPT),
    ],
    spell_icon_id=310,
    notes='NEW (druid-rework BALANCE §6 row 1,0 capstone buff, rank 3/3)',
    raw_overrides={'SpellClassSet': 7, 'ProcChance': 101, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Spirit increased by $s1% and mana regeneration while casting increased by $s2%.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Spirit increased by $s1% and mana regeneration while casting increased by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


gale_winds_stack_200351 = spell(
    id=200351,
    name='Gale Winds',
    school=School.NORMAL,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=2837,
    notes='NEW (druid-rework BALANCE §6 row 8,3 capstone buff): PLAN §0.2 - pure data, CumulativeAura re-applies the mod on each stack change (amount x stacks); cast by spell_dru_hurricane_tick/_channel on 42231/16914 (WP-B)',
    raw_overrides={'CumulativeAura': 5, 'SpellClassSet': 7, 'ProcChance': 101, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': HURRICANE, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Hurricane damage increased by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Hurricane damage increased by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


astral_crit_200354 = spell(
    id=200354,
    name='Astral Crit',
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
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=SpellModOp.CRITICAL_CHANCE),
    ],
    spell_icon_id=225,
    notes='NEW hidden linked passive (CORE-AUDIT row 5, druid-rework BALANCE §6 row 1,2 correction item 2): Improved Moonfire r1\'s Arcane crit reaching Astral spells; linked_spell(16821, 200354, type=2) in druid_talents.py',
    raw_overrides={'SpellClassSet': 7, 'ProcChance': 101, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_2': STARFALL, 'EffectSpellClassMaskA_3': STARSURGE | FURY_OF_ELUNE, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712188, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


astral_crit_200355 = spell(
    id=200355,
    name='Astral Crit',
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
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=107, misc_value=SpellModOp.CRITICAL_CHANCE),
    ],
    spell_icon_id=225,
    notes='NEW hidden linked passive (CORE-AUDIT row 5): Improved Moonfire r2; linked_spell(16822, 200355, type=2) in druid_talents.py',
    raw_overrides={'SpellClassSet': 7, 'ProcChance': 101, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_2': STARFALL, 'EffectSpellClassMaskA_3': STARSURGE | FURY_OF_ELUNE, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712188, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


astral_crit_200356 = spell(
    id=200356,
    name='Astral Crit',
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
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=107, misc_value=SpellModOp.CRITICAL_CHANCE),
    ],
    spell_icon_id=225,
    notes='NEW hidden linked passive (CORE-AUDIT row 5): Improved Moonfire r3 (200323); linked_spell(200323, 200356, type=2) in druid_talents.py',
    raw_overrides={'SpellClassSet': 7, 'ProcChance': 101, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_2': STARFALL, 'EffectSpellClassMaskA_3': STARSURGE | FURY_OF_ELUNE, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712188, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


# --- Starfire cleave + Fury of Elune's triggered parts (BALANCE.md §4, §5) ---

starfire_cleave_200337 = spell(
    id=200337,
    name='Starfire',
    school=School.ARCANE,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,  # script-cast on a unit: RangeIndex 0 = 0yd, fails CheckRange
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=185.4, potency_kind='direct', implicit_target_a=53, implicit_target_b=16, radius_yards=8.0),
    ],
    spell_icon_id=1485,
    notes='NEW (druid-rework BALANCE §4 "Starfire cleave"): half of 2912\'s own base/ppl (120/29/14.3 -> 59/15/7.15); shares Starfire\'s family bit deliberately (Tentacle Mind Flay precedent); scripted_by(spell_dru_starfall_aoe) reuses the stock area-target filter that drops GetExplTargetUnit() (see druid_talents.py); cast by spell_dru_starfire_cleave AfterHit on 2912 (WP-B). Potency system P5 (druid pass): converted to sp_potency=185.4 (potency-report default, base/coef already agreed); the old bonus_coefficients(direct=0.5) spell_bonus_data override is retired in favor of the generated DBC coefficient. This spell previously had no explicit BaseLevel/SpellLevel/MaxLevel (defaulted to 0) since it is never learned or cast directly - potency requires SpellLevel set (BaseLevel must equal it, "Caveats and checks"), so added BaseLevel=SpellLevel=20/MaxLevel=80 matching Starfire 2912\'s own SpellLevel (this is conceptually half of that spell).',
    raw_overrides={'BaseLevel': 20, 'SpellLevel': 20, 'MaxLevel': 80, 'DefenseType': 1, 'SpellClassSet': 7, 'ProcChance': 101, 'MaxTargets': 2, 'EquippedItemClass': -1, 'SpellClassMask_1': STARFIRE, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes {pot1} Arcane damage to the target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


fury_of_elune_beam_200338 = spell(
    id=200338,
    name='Fury of Elune',
    school=School.ARCANE | School.NATURE,  # Astral
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,  # script-cast on a unit: RangeIndex 0 = 0yd, fails CheckRange
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=15.0, potency_kind='direct', implicit_target_a=6),
    ],
    spell_icon_id=90111,
    notes='NEW (druid-rework BALANCE §5 "Fury of Elune"): live damage every 0.5s tick, scales with level (learn 60, level-60 value 40 -> ppl 40/60); cast by the 200336 AuraScript\'s OnEffectPeriodic (WP-B); SpellVisualID_1 90020 (patch_druid_vfx_models.py): stock Moonfire impact + Fury of Elune damage-impact sound on every tick, under the beam 200336 carries. Potency system P5 (druid pass): converted to sp_potency=15.0 (potency-report default, base/coef already agreed); the old bonus_coefficients(direct=0.1) spell_bonus_data override is retired in favor of the generated DBC coefficient.',
    raw_overrides={'BaseLevel': 60, 'SpellLevel': 60, 'MaxLevel': 80, 'DefenseType': 1, 'SpellClassSet': 7, 'ProcChance': 101, 'SpellClassMask_3': FURY_OF_ELUNE, 'SpellVisualID_1': 90020, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes {pot1} Astral damage to the target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


fury_of_elune_splash_200339 = spell(
    id=200339,
    name='Fury of Elune',
    school=School.ARCANE | School.NATURE,  # Astral
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,  # script-cast on a unit: RangeIndex 0 = 0yd, fails CheckRange
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=7.5, potency_kind='direct', implicit_target_a=53, implicit_target_b=16, radius_yards=8.0),
    ],
    spell_icon_id=90111,
    notes='NEW (druid-rework BALANCE §5): half of 200338, scripted_by(spell_dru_starfall_aoe) filters the primary target out (see druid_talents.py). Potency system P5 (druid pass): converted to sp_potency=7.5 (potency-report default, base/coef already agreed); the old bonus_coefficients(direct=0.05) spell_bonus_data override is retired in favor of the generated DBC coefficient.',
    raw_overrides={'BaseLevel': 60, 'SpellLevel': 60, 'MaxLevel': 80, 'DefenseType': 1, 'SpellClassSet': 7, 'ProcChance': 101, 'SpellClassMask_3': FURY_OF_ELUNE, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes {pot1} Astral damage to the target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


celestial_alignment_200340 = spell(
    id=200340,
    name='Celestial Alignment',
    school=School.NORMAL,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=1, apply_aura=108, misc_value=SpellModOp.COOLDOWN),
    ],
    spell_icon_id=2013,
    notes='NEW (druid-rework BALANCE §5 "200340 Celestial Alignment"): cast by Fury of Elune\'s SpellScript OnCast with BP0 = the caster\'s Eclipse rank eff1 amount (30 if untalented, WP-B); eff2 halves the Starsurge cooldown while up',
    raw_overrides={'SpellClassSet': 7, 'ProcChance': 101, 'EquippedItemClass': -1, 'EffectSpellClassMaskB_3': STARSURGE, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Grants the benefits of both Solar and Lunar Eclipse, and halves the cooldown of Starsurge.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Grants the benefits of both Solar and Lunar Eclipse, and halves the cooldown of Starsurge.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


# --- Resto WP-0 pulls (druid-rework.RESTO.md §3 item 1) ---
# Referenced by druid_talents.py's Tree of Life talent rank=[65139] as a bare int today; this pull
# makes it a real declared row. Tooltip-only edit in the Resto pass (RESTO §8 (8,1)); the two
# LEARN_SPELL effects teach 33891 (druid_spells.py) and 5420 (below).
tree_of_life_65139 = spell(
    id=65139,
    name='Tree of Life',
    school=School.NORMAL,
    attributes=8651136,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.LEARN_SPELL, die_sides=0, implicit_target_a=1, trigger_spell=33891),
    ],
    spell_icon_id=2257,
    notes="pulled from existing data; druid-rework RESTO §7 '65139 (ToL talent rank)': tooltip only - Tree of Life is a transform buff now, not a shapeshift (CORE-AUDIT row 38), so the tooltip drops the shapeshift/cast-restriction wording. Code-review fix: dropped the second LEARN_SPELL(5420) effect - 5420's bonuses already ride along only while 33891 is active via linked_spell(33891, 5420, type=2) in druid_talents.py; permanently learning 5420 here made its -20% HoT cost/-50% Healing Touch cast time/+25% Regrowth crit bonuses apply at all times, not just while shapeshifted into Tree of Life.",
    raw_overrides={'AttributesEx': 2147483648, 'AttributesEx2': 1, 'AttributesEx4': 32768, 'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'EquippedItemClass': -1, 'SpellVisualID_1': 107, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your heal over time spells by $5420s1% and grants the ability to shift into the Tree of Life. See Tree of Life.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


# Also a legacy row in source/spells/npc.csv - deleted in this same change. CORE-AUDIT row 38: this
# rides along via linked_spell(33891, 5420, 2) instead of ShapeshiftMask once Tree of Life becomes a
# buff; WP-A drops the ShapeshiftMask=2 raw override and re-scopes eff1's classmask (RESTO §7).
tree_of_life_5420 = spell(
    id=5420,
    name='Tree of Life',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COST),
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.CASTING_TIME),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CRITICAL_CHANCE),
    ],
    spell_icon_id=2257,
    notes="druid-rework RESTO §7 row '5420 (ToL passive, learned by 65139)': eff1 keeps -20% SPELLMOD_COST, A-mask re-scoped to CORE_HOT_CAST (adds the CENARION_WARD bit so the ward's released heal's cost is also cut); eff2 -50% SPELLMOD_CASTING_TIME scoped to Healing Touch only (EffectSpellClassMaskB_1=HEALING_TOUCH). New eff3 (WP-B coordination, CORE-AUDIT row 13's literal text - RESTO.md's own tables omit this): flat CRITICAL_CHANCE +25%, scoped to Regrowth only (C_1=REGROWTH) - spell_dru_regrowth's AuraScript reads this via GetAuraEffect(5420, EFFECT_2) to correct Regrowth's periodic tick's snapshotted crit chance (the rider applies to the direct heal only, per RESTO §8 (8,1)). ShapeshiftMask=2 was already dropped by WP-0 (CORE-AUDIT row 38 - rides along via linked_spell(33891, 5420, 2) instead).",
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': CORE_HOT_CAST[0], 'EffectSpellClassMaskA_2': CORE_HOT_CAST[1], 'EffectSpellClassMaskA_3': CORE_HOT_CAST[2], 'EffectSpellClassMaskB_1': HEALING_TOUCH, 'EffectSpellClassMaskC_1': REGROWTH, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Passive', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712188, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 7, 'SpellClassMask_2': 134217728, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


# Already referenced by druid_trigger_spells.py as a bare int (16870, Omen of Clarity's
# PROC_TRIGGER_SPELL target); also a legacy row in source/spells/npc.csv - deleted in this same
# change. Resto's WP-A adds the BLOOM/CENARION_WARD bits to eff1's EffectSpellClassMaskA_* so Bloom
# and Cenarion Ward's release consume it too (RESTO §7).
clearcasting_16870 = spell(
    id=16870,
    name='Clearcasting',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=262144,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=14),
    ],
    spell_icon_id=212,
    notes="pulled from existing data; druid-rework RESTO §7 '16870 Clearcasting': add the BLOOM and CENARION_WARD bits to eff1's EffectSpellClassMaskA_3 so Bloom (200560/200561) and Cenarion Ward's release (200562/200563) also consume a Clearcasting charge (Flourish 200564 deliberately left out, Q25 - it does not heal directly).",
    raw_overrides={'AttributesEx2': 4, 'AttributesEx3': 1073938432, 'CastingTimeIndex': 1, 'ProcTypeMask': 87376, 'ProcChance': 100, 'ProcCharges': 1, 'BaseLevel': 10, 'SpellLevel': 10, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 14924799, 'EffectSpellClassMaskA_2': 126879699, 'EffectSpellClassMaskA_3': 263168 | BLOOM | CENARION_WARD, 'SpellVisualID_1': 2736, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': "Each of the Druid's damage, healing spells and auto attacks has a chance of causing the caster to enter a Clearcasting state.  The Clearcasting state reduces the Mana, Rage or Energy cost of your next damage, healing spell or offensive ability by $16870s1%.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next damage or healing spell or offensive ability has its mana, rage or energy cost reduced by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 7, 'SpellClassMask_2': 2097152, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


# Revitalize's Runic Power tick (RESTO §7 "48543 (Revitalize runic power)"): base 159 -> 79 (8 RP)
# in WP-A. Referenced today only via the tooltip's $/10;48543s1 token.
revitalize_48543 = spell(
    id=48543,
    name='Revitalize',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=134217728,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=EffectType.ENERGIZE, base_points=79, implicit_target_a=21, misc_value=6),
    ],
    spell_icon_id=2862,
    notes="pulled from existing data; druid-rework RESTO §7 '48543 (Revitalize runic power)': base 159->79 (8 RP)",
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 60, 'SpellLevel': 60, 'DurationIndex': 0, 'EquippedItemClass': -1, 'SpellVisualID_1': 86, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Your Rejuvenation and Wild Growth spells have a chance to restore $48540s1 Energy, $/10;48541s1 Rage, $48542s1% Mana or $/10;48543s1 Runic Power per tick.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


# ============================================================================
# druid-rework RESTO WP-A: new standalone/baseline spells (RESTO §2.1, §6, §7)
# ============================================================================

bloom_jump_200561 = spell(
    id=200561,
    name='Bloom',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.HEAL, sp_potency=23.6, potency_kind='heal', implicit_target_a=21),
    ],
    spell_icon_id=90130,
    notes="druid-rework RESTO §6 'Bloom (200560 castable, 200561 jump)': the jump copy Druid::StartBloomJumps casts on each wave's targets - identical formula/mask to 200560, no cost/cooldown, range_yards=100 (script-cast, docs/bugs-and-fixes.md 'works on yourself only'), AttributesEx3 |= 0x200 (NOT_A_PROC, so triggered jumps can still roll Living Seed/Omen of Clarity/Natural Perfection/Nature's Grace). A lobbed projectile (Speed 25, SpellVisualID_1 90024: the Bloom orb with no CastKit) - StartBloomJumps casts it from the previous target with the druid as original caster, so the orb bounces target to target while the heal, crit and procs stay the druid's. Potency system P5 (druid pass): converted to sp_potency=23.6, same as 200560 (potency-report default, base/coef already agreed); the old bonus_coefficients(direct=0.75) spell_bonus_data override (and the redundant hand-set EffectBonusMultiplier_1) are retired in favor of the generated DBC coefficient.",
    raw_overrides={'AttributesEx3': 512, 'BaseLevel': 39, 'SpellLevel': 39, 'MaxLevel': 80, 'DefenseType': 1, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 7, 'SpellClassMask_3': BLOOM, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals a friendly target for {pot1}.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'SpellVisualID_1': 90024, 'Speed': 25.0},
)


cenarion_ward_heal_200563 = spell(
    id=200563,
    name='Cenarion Ward',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, sp_potency=23.6, potency_kind='heal_periodic', implicit_target_a=21, apply_aura=AuraType.PERIODIC_HEAL, amplitude=2000),
    ],
    spell_icon_id=198,
    notes="druid-rework RESTO §6 'Cenarion Ward (200562 ward, 200563 heal)': the released heal over time - a core HoT and a Harmony stack, unlike the ward itself. spell_dru_cenarion_ward's OnEffectProc casts this with the ORIGINAL caster preserved as the aura caster (CastSpell aurEff/originalCaster overload), so it counts toward Harmony and scales off the druid's own spell power. range_yards=100 (script-cast, plain CastSpell - no CastCustomSpell override, so the potency hook applies normally). Potency system P5 (druid pass): converted to sp_potency=23.6 (potency-report default, base/coef already agreed); the old bonus_coefficients(dot=1.0) spell_bonus_data override (and the redundant hand-set EffectBonusMultiplier_1) are retired in favor of the generated DBC coefficient.",
    raw_overrides={'BaseLevel': 38, 'SpellLevel': 38, 'MaxLevel': 80, 'DefenseType': 1, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 7, 'SpellClassMask_3': CENARION_WARD_HOT, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals the target for {pot1.total} over $d.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Heals {pot1} damage every $t1 seconds.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


flourish_ground_200603 = spell(
    id=200603,
    name='Flourish',
    school=School.NATURE,
    attributes=0x80 | 0x100,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=1500,
    effects=[
        Effect(type=EffectType.PERSISTENT_AREA_AURA, base_points=0, implicit_target_a=18, implicit_target_b=29, apply_aura=AuraType.DUMMY, radius_yards=5.0),
    ],
    spell_icon_id=90131,
    notes="Visual only: the Efflorescence ground effect at the caster's feet when Flourish is cast, triggered by flourish_buff_200565's eff2. A 1.5 s ground zone (TARGET_DEST_CASTER / TARGET_DEST_DYNOBJ_ALLY, the shape of stock 'Tower Buff' 23467) whose PersistentAreaKit (SpellVisualID_1 90022, patch_druid_vfx_models.py) shows Druid_Efflorescence_Persistent for the zone's lifetime. Its DUMMY aura does nothing; attributes DO_NOT_DISPLAY | DO_NOT_LOG keep it off buff bars and the combat log.",
    raw_overrides={'DefenseType': 0, 'PreventionType': 0, 'ProcChance': 101, 'SpellClassSet': 7, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'SpellVisualID_1': 90022},
)


flourish_buff_200565 = spell(
    id=200565,
    name='Flourish',
    school=School.NATURE,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.TRIGGER_SPELL, implicit_target_a=1, trigger_spell=flourish_ground_200603.id),
    ],
    spell_icon_id=90131,
    notes="druid-rework RESTO §6 'Flourish (200564 castable, 200565 buff)': eff2 triggers flourish_ground_200603, the Efflorescence ground visual at the caster's feet. Visible self buff for the 8 s acceleration window - UnitScript::OnAuraApply gives a HoT the caster newly applies while this buff is up the same injected ticks for the buff's remaining time (Q16). Code-review fix: attributes 192->0 - was PASSIVE|DO_NOT_DISPLAY, hiding a buff explicitly documented as visible.",
    raw_overrides={'DefenseType': 1, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 7, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your heal over time effects tick twice as fast.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your heal over time effects tick twice as fast.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


natural_alacrity_healing_buff_200566 = spell(
    id=200566,
    name='Natural Alacrity',
    school=School.NATURE,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=112,
    notes="druid-rework RESTO §7 '200566': the separate, non-consumed 10% Nature healing buff triggered by Natural Alacrity (17116) eff2 - not itself a charge, so it isn't eaten by the instant-cast proc. Code-review fix: attributes 192->0 - was PASSIVE|DO_NOT_DISPLAY, hiding a timed buff the player needs to see.",
    raw_overrides={'DefenseType': 1, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 7, 'EffectSpellClassMaskA_1': HEAL_DIRECT[0], 'EffectSpellClassMaskA_2': HEAL_DIRECT[1], 'EffectSpellClassMaskA_3': HEAL_DIRECT[2], 'EffectSpellClassMaskB_1': HEAL_DOT[0], 'EffectSpellClassMaskB_2': HEAL_DOT[1], 'EffectSpellClassMaskB_3': HEAL_DOT[2], 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The effectiveness of your Nature healing spells is increased by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'The effectiveness of your Nature healing spells is increased by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


cultivation_200567 = spell(
    id=200567,
    name='Cultivation',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, sp_potency=3.5, potency_kind='heal_periodic', implicit_target_a=21, apply_aura=AuraType.PERIODIC_HEAL, amplitude=2000),
    ],
    spell_icon_id=3282,
    notes="druid-rework RESTO §8 (1,0) 'Nature's Mending' capstone: applied by spell_dru_rejuvenation's OnEffectPeriodic when the caster knows 200582 and the target is below 50% health. A core HoT and a Harmony stack, but Harmony itself is never enabled for it. range_yards=100 (script-cast, plain CastSpell - no CastCustomSpell override, so the potency hook applies normally). Potency system P5 (druid pass): converted to sp_potency=3.5 (potency-report default, base/coef already agreed); the old bonus_coefficients(dot=0.1) spell_bonus_data override (and the redundant hand-set EffectBonusMultiplier_1) are retired in favor of the generated DBC coefficient.",
    raw_overrides={'BaseLevel': 17, 'SpellLevel': 17, 'MaxLevel': 80, 'DefenseType': 1, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 7, 'SpellClassMask_3': CULTIVATION, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals the target for {pot1.total} over $d.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Heals {pot1} damage every $t1 seconds.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


germination_200568 = spell(
    id=200568,
    name='Germination',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=40.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, sp_potency=10.5, potency_kind='heal_periodic', implicit_target_a=21, apply_aura=AuraType.PERIODIC_HEAL, amplitude=3000),
    ],
    spell_icon_id=1216,
    notes="druid-rework RESTO §8 (7,1) 'Proliferation' capstone: a second, distinct Rejuvenation aura - identical effect/coefficient to 774, deliberately sharing REJUVENATION's family bit (dword1 0x10, not a new bit) so every Rejuvenation SpellMod reaches it too; code tells the two apart by spell id, not by mask. Applied by spell_dru_rejuvenation via PreventHitAura+CastSpell when the target already has 774 (or refreshed directly when both exist), always TRIGGERED so cost/cast time never matter - mana_cost_pct 0 (not 18 like 774) purely to keep generate.py's looks_player_castable lint from flagging this hidden-only spell as missing a SkillLineAbility row (it is never learned or cast directly). Potency system P5 (druid pass): converted to sp_potency=10.5, same as 774 (potency-report default, base/coef already agreed).",
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx3': 128, 'AttributesEx4': 1048576, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Heals {pot1} damage every $t1 seconds.', 'BaseLevel': 4, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A second Rejuvenation, counted separately.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 0, 'ShapeshiftMask': 2, 'SpellClassMask_1': REJUVENATION, 'SpellClassSet': 7, 'SpellDescriptionVariableID': 176, 'SpellLevel': 4, 'SpellVisualID_1': 32, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


yseras_gift_heal_200569 = spell(
    id=200569,
    name="Ysera's Gift",
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(
            type=EffectType.HEAL, base_points=0, implicit_target_a=21,
            potency_excluded="script-driven: amount is computed entirely in spell_dru_yseras_gift "
            "(a percent of the druid's own max health) and passed as BP0 via CastCustomSpell, which "
            "always wins over CalcValue/the potency hook (D2). Giving this effect a potency value "
            "would be dead data the hook never reaches - same category as the Warlock pilot's "
            "percent-of-max-health exclusions (potency-system.PROGRESS.md P4).",
        ),
    ],
    spell_icon_id=2067,
    notes="druid-rework RESTO §8 (1,2) 'Ysera's Gift': amount computed entirely in spell_dru_yseras_gift (% of the druid's own max health) and passed as BP0 via CastCustomSpell - bonus_coefficients(direct=0) so percent healing mods still apply even though the base is 0. DmgClass MAGIC so it can crit. Never a direct Nature heal (Heal::IsDirectNatureHeal's never-list) and never a Harmony stack. range_yards=100 (script-cast, self or an ally). Potency system P5 (druid pass): NOT converted - script-driven percent-of-max-health effect (F8/D2), same category as the Warlock pilot's percent-of-max-health exclusions. The bonus_coefficients(direct=0) call is untouched (not a potency mechanism - it exists so percent healing mods still apply to the 0 base).",
    raw_overrides={'DefenseType': 1, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 7, 'SpellClassMask_3': YSERAS_GIFT, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals for $s1.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
bonus_coefficients(yseras_gift_heal_200569, direct=0)


proliferation_buff_200570 = spell(
    id=200570,
    name='Proliferation',
    school=School.NATURE,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2585,
    notes="druid-rework RESTO §8 (7,1) 'Proliferation': self buff, one charge, consumed by the next Rejuvenation cast's spread (spell_dru_rejuvenation's AfterHit). Not a stacking aura - a new proc simply refreshes it. Code-review fix: attributes 192->0 - was PASSIVE|DO_NOT_DISPLAY, hiding the proc window the player needs to see to know their next Rejuvenation will spread.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next Rejuvenation also applies to 2 nearby allies.', 'DefenseType': 1, 'PreventionType': 1, 'ProcChance': 101, 'ProcCharges': 1, 'SpellClassSet': 7, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your next Rejuvenation also applies to 2 nearby allies.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


living_spirit_stat_200571 = spell(
    id=200571,
    name='Living Spirit',
    school=School.NATURE,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=4),
    ],
    spell_icon_id=2011,
    notes="druid-rework RESTO §8 (6,0) capstone: self buff, 1% Spirit per stack, stack count = Druid::CountActiveRejuvenations (self + group), no cap beyond the design's 10.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your Spirit is increased.', 'CumulativeAura': 10, 'DefenseType': 1, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 7, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Spirit is increased.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


clearcasting_omen_200572 = spell(
    id=200572,
    name='Clearcasting',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=262144,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=212,
    notes="druid-rework RESTO §8 (2,1) Omen of Clarity r3's Clearcasting variant: a clone of 16870's cost-reduction masking (including the BLOOM/CENARION_WARD bits, with the retired Nourish dword-2 bit dropped from A_2 - CORE-AUDIT §4 inert-key list, this is new-rework content) plus eff2 APPLY_AURA+DUMMY stored 9 (the capstone's +10% damage/healing), read by Druid::ConsumedEmpoweredClearcasting via m_spellModTakingSpell at cast completion - never given a DAMAGE/DOT SpellMod itself (a triggered 0-cost spell would otherwise eat the charge). Code-review fix: eff2 was a plain SPELL_EFFECT_DUMMY effect, so GetAuraEffect(200572, EFFECT_1) always returned null and the capstone's +10% never applied.",
    raw_overrides={'AttributesEx2': 4, 'AttributesEx3': 1073938432, 'CastingTimeIndex': 1, 'ProcTypeMask': 87376, 'ProcChance': 100, 'ProcCharges': 1, 'BaseLevel': 10, 'SpellLevel': 10, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 14924799, 'EffectSpellClassMaskA_2': 93325267, 'EffectSpellClassMaskA_3': 263168 | BLOOM | CENARION_WARD, 'SpellVisualID_1': 2736, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'NameSubtext_Lang_enUS': '', 'Description_Lang_enUS': "Reduces the Mana, Rage or Energy cost of your next damaging or healing spell or offensive ability by 100% and increases its damage or healing by 10%.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next damage or healing spell or offensive ability costs no resource and deals 10% more damage or healing.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 7, 'SpellClassMask_2': 2097152, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


natural_shapeshifter_healing_buff_200573 = spell(
    id=200573,
    name='Natural Shapeshifter',
    school=School.NATURE,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=122,
    notes="druid-rework RESTO §8 (0,2) 'Natural Shapeshifter' no-form/Tree-of-Life healing bonus: amount set dynamically from the talent's eff2 by Druid::ApplyShapeshiftFormBonuses, applied only with no form or during Tree of Life and removed otherwise (CORE-AUDIT row 16).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your healing is increased.', 'DefenseType': 1, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 7, 'EffectSpellClassMaskA_1': HEAL_DIRECT[0], 'EffectSpellClassMaskA_2': HEAL_DIRECT[1], 'EffectSpellClassMaskA_3': HEAL_DIRECT[2], 'EffectSpellClassMaskB_1': HEAL_DOT[0], 'EffectSpellClassMaskB_2': HEAL_DOT[1], 'EffectSpellClassMaskB_3': HEAL_DOT[2], 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your healing is increased.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


tree_of_life_rejuv_heal_200574 = spell(
    id=200574,
    name='Tree of Life',
    school=School.NATURE,
    attributes=196608,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(
            type=EffectType.HEAL, base_points=0, implicit_target_a=21,
            potency_excluded="script-driven: amount = the Rejuvenation aura's own tick amount x total "
            "ticks x 25%, computed in Druid::OnRejuvenationApplied and passed as BP0 via "
            "CastCustomSpell, which always wins over CalcValue/the potency hook (D2). Same category "
            "as Ysera's Gift (200569) above and the Warlock pilot's percent-of-other-effect "
            "exclusions (potency-system.PROGRESS.md P4).",
        ),
    ],
    spell_icon_id=2257,
    notes="druid-rework RESTO §8 (8,1) 'Tree of Life' instant Rejuvenation heal: amount = the Rejuvenation aura's own tick amount x total ticks x 25%, computed in Druid::OnRejuvenationApplied and passed as BP0. AttributesEx3 |= 0x20000000 (IGNORE_CASTER_MODIFIERS) so the caster's healing-done mods (already folded into the computed amount) aren't applied a second time. Never a direct Nature heal. RESTO's 'DmgClass NONE so it cannot crit' can't be set directly (this pipeline's Spell.dbc struct has no writable DmgClass column) - fixed instead (WP-C) with the dedicated AttributesEx2 |= SPELL_ATTR2_CANT_CRIT (0x20000000, SharedDefines.h:473), which achieves the same 'never crits' behaviour as a real spell attribute rather than needing a C++ workaround in the CastCustomSpell call. Potency system P5 (druid pass): NOT converted - script-driven percent-of-another-effect's-total (F8/D2), same category as Ysera's Gift above.",
    raw_overrides={'AttributesEx2': 536870912, 'AttributesEx3': 536870912, 'DefenseType': 1, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 7, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals the target for $s1.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


revitalize_mana_200575 = spell(
    id=200575,
    name='Revitalize',
    school=School.NATURE,
    attributes=134217728,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=EffectType.ENERGIZE, base_points=0, implicit_target_a=1, misc_value=0),
    ],
    spell_icon_id=2862,
    notes="druid-rework RESTO §8 (8,0) 'Revitalize' caster-side mana return: 1% of the caster's base mana, cast on the caster with a computed BP0 (CalculatePct(caster->GetCreateMana(), 1)) every time either DUMMY effect on 48539-48545 fires.",
    raw_overrides={'DefenseType': 1, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 7, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Restores mana.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


tranquil_focus_200576 = spell(
    id=200576,
    name='Tranquil Focus',
    school=School.NATURE,
    attributes=196608,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.EFFECT_IMMUNITY, misc_value=98),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.EFFECT_IMMUNITY, misc_value=144),
    ],
    spell_icon_id=963,
    notes="druid-rework RESTO §8 (0,1) 'Nature's Focus' capstone buff: spell_dru_natures_focus_capstone applies this on Tranquility (740) EFFECT_1 REAL apply when the caster knows the final rank (17065) and removes it with the aura. -50% damage taken plus knockback (98) and stun (144) effect immunity while channeling.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Take 50% less damage and cannot be knocked back.', 'DefenseType': 1, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 7, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Take 50% less damage and cannot be knocked back.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


# ============================================================================
# druid-rework RESTO WP-A: new talent-rank spells (RESTO §2.1/§8)
# ============================================================================

def _dru_passive_talent_kwargs():
    return dict(school=School.NORMAL, attributes=464, cast_time_ms=0, cooldown_ms=0,
                category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0, duration_ms=-1)


natures_resilience_200577 = spell(
    id=200577, name="Nature's Resilience", **_dru_passive_talent_kwargs(),
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.MOD_CUSTOM_STAT_PCT, misc_value=2097152)],
    spell_icon_id=1675,
    notes="druid-rework RESTO §8 (0,3) NEW, was Furor (822): percentage Versatility (MOD_CUSTOM_STAT_PCT misc 1<<21, CR_VERSATILITY), not rating.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your Versatility is increased.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Versatility by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)
natures_resilience_200578 = spell(
    id=200578, name="Nature's Resilience", **_dru_passive_talent_kwargs(),
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_CUSTOM_STAT_PCT, misc_value=2097152)],
    spell_icon_id=1675,
    notes='druid-rework RESTO §8 (0,3): rank 2 of the rewrite above.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your Versatility is increased.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Versatility by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)
natures_resilience_200579 = spell(
    id=200579, name="Nature's Resilience", **_dru_passive_talent_kwargs(),
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MOD_CUSTOM_STAT_PCT, misc_value=2097152)],
    spell_icon_id=1675,
    notes='druid-rework RESTO §8 (0,3): rank 3 of the rewrite above.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your Versatility is increased.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Versatility by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


natures_mending_200580 = spell(
    id=200580, name="Nature's Mending", **_dru_passive_talent_kwargs(),
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.DUMMY)],
    spell_icon_id=1929,
    notes="druid-rework RESTO §8 (1,0) NEW, was Master Shapeshifter (1915): APPLY_AURA+DUMMY marker read by Druid::GetDirectHealMultiplier/ApplyPeriodicHealTickMods, a plain multiplier (PLAN A2) applied when the target is below 50% health at calc time. Code-review fix: was a plain SPELL_EFFECT_DUMMY effect, which creates no AuraEffect at all, so GetRankAmount()'s GetAuraEffect(id, EFFECT_0) lookup always returned null.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your Rejuvenation and Regrowth heal more on injured targets.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Rejuvenation and Regrowth heal targets below 50% health for $s1% more.\n\n|cFF9D9D9DCapstone Bonus: When your Rejuvenation heals a target below 50% health, it applies Cultivation, healing them for 150 plus 0.3 spell power over 6 sec.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)
natures_mending_200581 = spell(
    id=200581, name="Nature's Mending", **_dru_passive_talent_kwargs(),
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY)],
    spell_icon_id=1929,
    notes='druid-rework RESTO §8 (1,0): rank 2 of the rewrite above.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your Rejuvenation and Regrowth heal more on injured targets.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Rejuvenation and Regrowth heal targets below 50% health for $s1% more.\n\n|cFF9D9D9DCapstone Bonus: When your Rejuvenation heals a target below 50% health, it applies Cultivation, healing them for 150 plus 0.3 spell power over 6 sec.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)
natures_mending_200582 = spell(
    id=200582, name="Nature's Mending", **_dru_passive_talent_kwargs(),
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1929,
    notes='druid-rework RESTO §8 (1,0): rank 3, the final/capstone rank - new eff2 DUMMY stored 0 is the Cultivation-enabled flag spell_dru_rejuvenation reads (HasAura(200582)).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your Rejuvenation and Regrowth heal more on injured targets.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your Rejuvenation and Regrowth heal targets below 50% health for $s1% more.\n\nCapstone Bonus: When your Rejuvenation heals a target below 50% health, it applies Cultivation, healing them for 150 plus 0.3 spell power over 6 sec.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


deep_roots_200583 = spell(
    id=200583, name='Deep Roots', **_dru_passive_talent_kwargs(),
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=999, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.DURATION),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=2669,
    notes='druid-rework RESTO §8 (1,1) NEW, was Subtlety (841), same position: both SpellMods scoped to REGROWTH (also reach Nature\'s Bounty spread copies, caster-side mods).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': "Your Regrowth's heal over time lasts longer and heals more.", 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the duration of your Regrowth's heal over time by $/1000;s1 sec and its healing by $s2%.\n\n|cFF9D9D9DCapstone Bonus: Your Regrowth costs 25% less mana when cast on a target already affected by your Regrowth.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': REGROWTH, 'EffectSpellClassMaskB_1': REGROWTH, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)
deep_roots_200584 = spell(
    id=200584, name='Deep Roots', **_dru_passive_talent_kwargs(),
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1999, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.DURATION),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=2669,
    notes='druid-rework RESTO §8 (1,1): rank 2 of the rewrite above.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': "Your Regrowth's heal over time lasts longer and heals more.", 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the duration of your Regrowth's heal over time by $/1000;s1 sec and its healing by $s2%.\n\n|cFF9D9D9DCapstone Bonus: Your Regrowth costs 25% less mana when cast on a target already affected by your Regrowth.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': REGROWTH, 'EffectSpellClassMaskB_1': REGROWTH, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)
deep_roots_200585 = spell(
    id=200585, name='Deep Roots', **_dru_passive_talent_kwargs(),
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2999, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.DURATION),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=2669,
    notes="druid-rework RESTO §8 (1,1): rank 3, the final/capstone rank. Code-review-pass cleanup: dropped a stray eff3 DUMMY stored 24 left over from an earlier draft, whose note pointed at Druid::ApplyPowerCostMods - that function (and the whole 'read a value off this talent's own effect' mechanism) was replaced by CORE-AUDIT row 15's actual design before this pass shipped: DruidDeepRootsCapstone::CanPrepare (druid_hooks.cpp) gates on HasAura(SPELL_DEEP_ROOTS_R3) alone and computes the -25% dynamically against deep_roots_cost_200602, so this talent's own rank spells need no capstone-carrying effect at all - eff3 was dead weight nothing ever read.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': "Your Regrowth's heal over time lasts longer and heals more.", 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the duration of your Regrowth's heal over time by $/1000;s1 sec and its healing by $s2%.\n\nCapstone Bonus: Your Regrowth costs 25% less mana when cast on a target already affected by your Regrowth.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': REGROWTH, 'EffectSpellClassMaskB_1': REGROWTH, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


yseras_gift_200586 = spell(
    id=200586, name="Ysera's Gift", **_dru_passive_talent_kwargs(),
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=5000)],
    spell_icon_id=2067,
    notes='druid-rework RESTO §8 (1,2) NEW: periodic trigger read by spell_dru_yseras_gift.OnEffectPeriodic (% of max health, self if not full else the lowest-HP% ally in range).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'You are periodically healed.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Every 5 sec, heals you for $s1% of your maximum health. If you are at full health, the most injured nearby ally is healed instead.\n\n|cFF9D9D9DCapstone Bonus: Ysera\'s Gift heals for 8% more for each of your active Rejuvenations.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)
yseras_gift_200587 = spell(
    id=200587, name="Ysera's Gift", **_dru_passive_talent_kwargs(),
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=5000)],
    spell_icon_id=2067,
    notes='druid-rework RESTO §8 (1,2): rank 2 of the rewrite above.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'You are periodically healed.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Every 5 sec, heals you for $s1% of your maximum health. If you are at full health, the most injured nearby ally is healed instead.\n\n|cFF9D9D9DCapstone Bonus: Ysera\'s Gift heals for 8% more for each of your active Rejuvenations.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)
yseras_gift_200588 = spell(
    id=200588, name="Ysera's Gift", **_dru_passive_talent_kwargs(),
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=5000),
        Effect(type=EffectType.DUMMY, base_points=7, implicit_target_a=1),
    ],
    spell_icon_id=2067,
    notes='druid-rework RESTO §8 (1,2): rank 3, the final/capstone rank - new eff2 DUMMY stored 7 (Waking Dream: +8% per active Rejuvenation, read by the direct-heal hook when HasAura(200588)).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'You are periodically healed.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Every 5 sec, heals you for $s1% of your maximum health. If you are at full health, the most injured nearby ally is healed instead.\n\nCapstone Bonus: Ysera's Gift heals for 8% more for each of your active Rejuvenations.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


perennial_200589 = spell(
    id=200589, name='Perennial', **_dru_passive_talent_kwargs(),
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=1999, implicit_target_a=1, apply_aura=AuraType.DUMMY)],
    spell_icon_id=4118,
    notes="druid-rework RESTO §8 (1,3) NEW: DUMMY stores the per-cast extension cap in ms (2000/4000/6000 live); spell_dru_rejuvenation tracks _perennialUsedMs per aura instance, +2000 ms per extension while the target is at full health before the tick (Q7).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your Rejuvenation lasts longer on full-health targets.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "When your Rejuvenation heals a target at full health, its duration is increased by 2 sec, up to $/1000;s1 sec per cast.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)
perennial_200590 = spell(
    id=200590, name='Perennial', **_dru_passive_talent_kwargs(),
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=3999, implicit_target_a=1, apply_aura=AuraType.DUMMY)],
    spell_icon_id=4118,
    notes='druid-rework RESTO §8 (1,3): rank 2 of the rewrite above.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your Rejuvenation lasts longer on full-health targets.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "When your Rejuvenation heals a target at full health, its duration is increased by 2 sec, up to $/1000;s1 sec per cast.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)
perennial_200591 = spell(
    id=200591, name='Perennial', **_dru_passive_talent_kwargs(),
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=5999, implicit_target_a=1, apply_aura=AuraType.DUMMY)],
    spell_icon_id=4118,
    notes='druid-rework RESTO §8 (1,3): rank 3 of the rewrite above.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your Rejuvenation lasts longer on full-health targets.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "When your Rejuvenation heals a target at full health, its duration is increased by 2 sec, up to $/1000;s1 sec per cast.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


proliferation_200592 = spell(
    id=200592, name='Proliferation', **_dru_passive_talent_kwargs(),
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200570)],
    spell_icon_id=2585,
    notes='druid-rework RESTO §8 (7,1) NEW: procs_on() below carries the 10/20/30% chance; triggers 200570 (the buff), not the spread itself.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your Wild Growth casts have a chance to empower your next Rejuvenation.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Wild Growth casts have a $h% chance to cause your next Rejuvenation within 15 sec to also apply to the 2 nearby allies with the lowest health that are not affected by your Rejuvenation.\n\n|cFF9D9D9DCapstone Bonus: Germination. Your Rejuvenation can be applied to a target twice. The second application counts as a separate heal over time effect. Recasting refreshes whichever has less time remaining.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'RangeIndex': 1, 'SpellClassSet': 7},
)
proliferation_200593 = spell(
    id=200593, name='Proliferation', **_dru_passive_talent_kwargs(),
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200570)],
    spell_icon_id=2585,
    notes='druid-rework RESTO §8 (7,1): rank 2 of the rewrite above.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your Wild Growth casts have a chance to empower your next Rejuvenation.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Wild Growth casts have a $h% chance to cause your next Rejuvenation within 15 sec to also apply to the 2 nearby allies with the lowest health that are not affected by your Rejuvenation.\n\n|cFF9D9D9DCapstone Bonus: Germination. Your Rejuvenation can be applied to a target twice. The second application counts as a separate heal over time effect. Recasting refreshes whichever has less time remaining.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'RangeIndex': 1, 'SpellClassSet': 7},
)
proliferation_200594 = spell(
    id=200594, name='Proliferation', **_dru_passive_talent_kwargs(),
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200570),
        Effect(type=EffectType.DUMMY, base_points=0, implicit_target_a=1),
    ],
    spell_icon_id=2585,
    notes='druid-rework RESTO §8 (7,1): rank 3, the final/capstone rank - new eff2 DUMMY stored 0 is the Germination-enabled flag spell_dru_rejuvenation reads (HasAura(200594)).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your Wild Growth casts have a chance to empower your next Rejuvenation.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your Wild Growth casts have a $h% chance to cause your next Rejuvenation within 15 sec to also apply to the 2 nearby allies with the lowest health that are not affected by your Rejuvenation.\n\nCapstone Bonus: Germination. Your Rejuvenation can be applied to a target twice. The second application counts as a separate heal over time effect. Recasting refreshes whichever has less time remaining.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'RangeIndex': 1, 'SpellClassSet': 7},
)
procs_on(proliferation_200592, proc_flags=PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS, family_name=7,
         family_mask=(0, WILD_GROWTH, 0), spell_phase_mask=PROC_SPELL_PHASE_CAST, chance=10)
procs_on(proliferation_200593, proc_flags=PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS, family_name=7,
         family_mask=(0, WILD_GROWTH, 0), spell_phase_mask=PROC_SPELL_PHASE_CAST, chance=20)
procs_on(proliferation_200594, proc_flags=PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS, family_name=7,
         family_mask=(0, WILD_GROWTH, 0), spell_phase_mask=PROC_SPELL_PHASE_CAST, chance=30)


photosynthesis_200595 = spell(
    id=200595, name='Photosynthesis', **_dru_passive_talent_kwargs(),
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE)],
    spell_icon_id=2861,
    notes="druid-rework RESTO §8 (8,2) NEW, was Improved Tree of Life (1930), same position: eff1 scoped to LIFEBLOOM's B-dword bit (A_2) - the only direct effect with that bit is the bloom (33778, flagged at load by SpellInfoCorrections.cpp:1246), so this only ever touches the bloom.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': "Your Lifebloom's bloom heals for more.", 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the healing of your Lifebloom's bloom by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Your Regrowth and Healing Touch casts on a target affected by your Lifebloom have a 20% chance to cause Lifebloom to bloom. This bloom does not end Lifebloom.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_2': LIFEBLOOM, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)
photosynthesis_200596 = spell(
    id=200596, name='Photosynthesis', **_dru_passive_talent_kwargs(),
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE)],
    spell_icon_id=2861,
    notes='druid-rework RESTO §8 (8,2): rank 2 of the rewrite above.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': "Your Lifebloom's bloom heals for more.", 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the healing of your Lifebloom's bloom by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Your Regrowth and Healing Touch casts on a target affected by your Lifebloom have a 20% chance to cause Lifebloom to bloom. This bloom does not end Lifebloom.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_2': LIFEBLOOM, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)
photosynthesis_200597 = spell(
    id=200597, name='Photosynthesis', **_dru_passive_talent_kwargs(),
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2861,
    notes='druid-rework RESTO §8 (8,2): rank 3, the final/capstone rank - new eff2 APPLY_AURA+DUMMY stored 19 (the 20% forced-bloom chance), read by spell_dru_photosynthesis_capstone (bound to 5185 and 8936). Code-review fix: eff2 was a plain SPELL_EFFECT_DUMMY effect, so GetAuraEffect(200597, EFFECT_1) always returned null and the forced bloom never happened.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': "Your Lifebloom's bloom heals for more.", 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the healing of your Lifebloom's bloom by $s1%.\n\nCapstone Bonus: Your Regrowth and Healing Touch casts on a target affected by your Lifebloom have a 20% chance to cause Lifebloom to bloom. This bloom does not end Lifebloom.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_2': LIFEBLOOM, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


unstoppable_growth_200598 = spell(
    id=200598, name='Unstoppable Growth', **_dru_passive_talent_kwargs(),
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.DUMMY)],
    spell_icon_id=2051,
    notes='druid-rework RESTO §8 (9,0) NEW, was Improved Barkskin (2264), same position: DUMMY read by spell_dru_wild_growth_aura::SetTickHeal (AddPct(_baseReduction, -GetRankAmount(UG)), same idiom as the T10 2P bonus); floored at -100% (Q18).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': "Your Wild Growth's healing falls off less over its duration.", 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Wild Growth's healing falls off $s1% less over its duration.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)
unstoppable_growth_200599 = spell(
    id=200599, name='Unstoppable Growth', **_dru_passive_talent_kwargs(),
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.DUMMY)],
    spell_icon_id=2051,
    notes='druid-rework RESTO §8 (9,0): rank 2 of the rewrite above.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': "Your Wild Growth's healing falls off less over its duration.", 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Wild Growth's healing falls off $s1% less over its duration.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7},
)


deep_roots_cost_200602 = spell(
    id=200602,
    name='Deep Roots',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COST),
    ],
    spell_icon_id=2669,
    notes="druid-rework RESTO §8 (1,1) capstone, per WP-B coordination (CORE-AUDIT row 15 / handoff message, not in RESTO.md's own tables): the hidden 1-charge cost-reduction aura an AllSpellScript::CanPrepare hook applies via CastCustomSpell (not a bare CastSpell) when the cast target already carries the caster's own Regrowth, and removes (RemoveAurasDueToSpell) otherwise - toggled per cast, not a permanent SpellMod. Flat COST scoped to Regrowth (8936) only. base_points here is an inert placeholder (delivers 0) - CORE-AUDIT row 15 requires the flat reduction to be exactly 25% of Regrowth's own *base* mana cost so that, combined with any other pct COST modifiers, the net effect is exactly ×0.75 regardless of level; a level-80-only static constant (a code-review finding caught this: the original -254 constant was calibrated to level-80's BaseMana=3496 and over-reduced the cost at lower levels) can't express that, so DruidDeepRootsCapstone::CanPrepare now computes int32(CalculatePct(player->GetCreateMana(), Regrowth's ManaCostPercentage)) fresh per cast, takes 25% of that, and passes it as a custom SPELLVALUE_BASE_POINT0 (the live value - SetSpellValue's CalcBaseValue takes the die_sides=1 point off itself). ProcCharges/ProcFlags are cosmetic only per WP-B (the CanPrepare hook drives apply/remove directly, not the DBC proc system).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your Regrowth costs less mana.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Regrowth costs less mana on a target already affected by your Regrowth.', 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': REGROWTH, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'ProcCharges': 1, 'ProcChance': 101, 'SpellClassSet': 7},
)


# --- druid-rework Feral pass WP-0 (FERAL §3 item 1 + §0.16): stock rows pulled verbatim with
# pull_dsl.py --constants. WP-A edits them; an untouched pulled row emits nothing.


sharpened_claws_16942 = spell(
    id=16942,
    name='Sharpened Claws',
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
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_PCT),
    ],
    spell_icon_id=1561,
    notes='druid-rework FERAL §7 (2,2): melee crit (aura 52) -> MOD_CRIT_PCT (290, crit with all spells and abilities), 2/4/6% unchanged, cat/bear/dire bear ShapeshiftMask kept.',
    raw_overrides={'ShapeshiftMask': SS_FERAL, 'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your critical strike chance with all spells and abilities while in Bear, Dire Bear or Cat Form by $s1%.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


sharpened_claws_16943 = spell(
    id=16943,
    name='Sharpened Claws',
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
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_PCT),
    ],
    spell_icon_id=1561,
    notes='druid-rework FERAL §7 (2,2): melee crit (aura 52) -> MOD_CRIT_PCT (290, crit with all spells and abilities), 2/4/6% unchanged, cat/bear/dire bear ShapeshiftMask kept.',
    raw_overrides={'ShapeshiftMask': SS_FERAL, 'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your critical strike chance with all spells and abilities while in Bear, Dire Bear or Cat Form by $s1%.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


sharpened_claws_16944 = spell(
    id=16944,
    name='Sharpened Claws',
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
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_PCT),
    ],
    spell_icon_id=1561,
    notes='druid-rework FERAL §7 (2,2): melee crit (aura 52) -> MOD_CRIT_PCT (290, crit with all spells and abilities), 2/4/6% unchanged, cat/bear/dire bear ShapeshiftMask kept.',
    raw_overrides={'ShapeshiftMask': SS_FERAL, 'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your critical strike chance with all spells and abilities while in Bear, Dire Bear or Cat Form by $s1%.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


primal_fury_37116 = spell(
    id=37116,
    name='Primal Fury',
    school=School.NORMAL,
    attributes=8651136,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.LEARN_SPELL, base_points=-1, implicit_target_a=1, trigger_spell=16958),
        Effect(type=EffectType.LEARN_SPELL, base_points=-1, implicit_target_a=1, trigger_spell=16952),
    ],
    spell_icon_id=146,
    notes="druid-rework FERAL §7 (3,2): tooltip only - mechanics unchanged (the taught procs' DBC ProcTypeMask 87380 has no DONE_PERIODIC and procs per target hit).",
    raw_overrides={'AttributesEx': 2147483648, 'AttributesEx2': 1, 'AttributesEx4': 32768, 'ShapeshiftMask': 145, 'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives you a $16958h% chance to gain an additional $/10;16959s1 Rage anytime you land a direct damage critical strike while in Bear Form or Dire Bear Form. Rage is granted per target hit. Your critical strikes from Cat Form abilities that add combo points have a $16952h% chance to add an additional combo point. Periodic damage does not trigger either clause.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


primal_fury_37117 = spell(
    id=37117,
    name='Primal Fury',
    school=School.NORMAL,
    attributes=8651136,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.LEARN_SPELL, base_points=-1, implicit_target_a=1, trigger_spell=16961),
        Effect(type=EffectType.LEARN_SPELL, base_points=-1, implicit_target_a=1, trigger_spell=16954),
    ],
    spell_icon_id=146,
    notes="druid-rework FERAL §7 (3,2): tooltip only - mechanics unchanged (the taught procs' DBC ProcTypeMask 87380 has no DONE_PERIODIC and procs per target hit).",
    raw_overrides={'AttributesEx': 2147483648, 'AttributesEx2': 1, 'AttributesEx4': 32768, 'ShapeshiftMask': 145, 'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives you a $16961h% chance to gain an additional $/10;16959s1 Rage anytime you land a direct damage critical strike while in Bear Form or Dire Bear Form. Rage is granted per target hit. Your critical strikes from Cat Form abilities that add combo points have a $16954h% chance to add an additional combo point. Periodic damage does not trigger either clause.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


heart_of_the_wild_17003 = spell(
    id=17003,
    name='Heart of the Wild',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=240,
    notes='druid-rework FERAL §7 (5,1), trimmed 5->3 ranks (17006/24894 orphaned): rank 1/3 - eff0 Intellect -> Agility 3/6/9% (misc 1: the stock icon-240/INT form-boost block goes inert, CORE-AUDIT row 32); eff1 plain DUMMY -> APPLY_AURA DUMMY 2/4/6% (form-boost BP of 24899/24900); raw eff3 cleared.',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Agility by $s1%. While in Cat Form your haste is increased by $s2%. While in Bear Form or Dire Bear Form your Stamina is increased by $s2% and your attack power is increased by $s2%.\n\n|cFF9D9D9DCapstone Bonus: While in Bear Form or Dire Bear Form, your maximum health is increased by $17005s3% of your Mastery, healing you receive from other players is increased by $17005s3% of your Mastery, and your Frenzied Regeneration heals for an additional $17005s3% of your Mastery. The external healing bonus is suppressed while Bestial Fury is active.|r', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


heart_of_the_wild_17004 = spell(
    id=17004,
    name='Heart of the Wild',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=240,
    notes='druid-rework FERAL §7 (5,1), trimmed 5->3 ranks (17006/24894 orphaned): rank 2/3 - eff0 Intellect -> Agility 3/6/9% (misc 1: the stock icon-240/INT form-boost block goes inert, CORE-AUDIT row 32); eff1 plain DUMMY -> APPLY_AURA DUMMY 2/4/6% (form-boost BP of 24899/24900); raw eff3 cleared.',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Agility by $s1%. While in Cat Form your haste is increased by $s2%. While in Bear Form or Dire Bear Form your Stamina is increased by $s2% and your attack power is increased by $s2%.\n\n|cFF9D9D9DCapstone Bonus: While in Bear Form or Dire Bear Form, your maximum health is increased by $17005s3% of your Mastery, healing you receive from other players is increased by $17005s3% of your Mastery, and your Frenzied Regeneration heals for an additional $17005s3% of your Mastery. The external healing bonus is suppressed while Bestial Fury is active.|r', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


heart_of_the_wild_17005 = spell(
    id=17005,
    name='Heart of the Wild',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=5000),
    ],
    spell_icon_id=240,
    notes='druid-rework FERAL §7 (5,1), trimmed 5->3 ranks (17006/24894 orphaned): rank 3/3 - eff0 Intellect -> Agility 3/6/9% (misc 1: the stock icon-240/INT form-boost block goes inert, CORE-AUDIT row 32); eff1 plain DUMMY -> APPLY_AURA DUMMY 2/4/6% (form-boost BP of 24899/24900); raw eff3 cleared; capstone eff2 PERIODIC_DUMMY 5 s, 50 = % of Mastery (CORE-AUDIT row 29, spell_dru_heart_of_the_wild_mastery refreshes max health on a Mastery change).',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Agility by $s1%. While in Cat Form your haste is increased by $s2%. While in Bear Form or Dire Bear Form your Stamina is increased by $s2% and your attack power is increased by $s2%.\n\nCapstone Bonus: While in Bear Form or Dire Bear Form, your maximum health is increased by $17005s3% of your Mastery, healing you receive from other players is increased by $17005s3% of your Mastery, and your Frenzied Regeneration heals for an additional $17005s3% of your Mastery. The external healing bonus is suppressed while Bestial Fury is active.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


leader_of_the_pack_24932 = spell(
    id=24932,
    name='Leader of the Pack',
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AREA_AURA_RAID, base_points=4, implicit_target_a=1, apply_aura=AuraType.MOD_WEAPON_CRIT_PERCENT, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AREA_AURA_RAID, base_points=3, implicit_target_a=1, apply_aura=AuraType.DUMMY, radius_yards=45.0),
        Effect(type=EffectType.APPLY_AREA_AURA_RAID, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MOD_RATING, misc_value=768, radius_yards=45.0),
    ],
    spell_icon_id=312,
    notes='druid-rework FERAL §7 (6,1): eff1 DUMMY -1 -> 3 (4% of base health heal, read by spell_dru_leader_of_the_pack_feral); DBC ProcTypeMask 4436 has no periodic flag.',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx4': 2097152, 'AttributesEx7': 268435456, 'ShapeshiftMask': 145, 'CastingTimeIndex': 1, 'ProcTypeMask': 4436, 'ProcChance': 100, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'While in Cat, Bear or Dire Bear Form, the Leader of the Pack increases ranged and melee critical chance of all party and raid members within $24932a1 yards by $24932s1%. Affected targets also heal themselves for $24932s2% of their base health when they land a direct damage critical strike, no more than once every 6 sec.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases ranged and melee critical chance by $s1%. Direct damage critical strikes heal you for $s2% of your base health, no more than once every 6 sec.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 7, 'SpellClassMask_2': 2048, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


heart_of_the_wild_bear_effect_24899 = spell(
    id=24899,
    name='Heart of the Wild Bear Effect',
    school=School.NORMAL,
    attributes=400,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MOD_ATTACK_POWER_PCT),
    ],
    spell_icon_id=0,
    notes='druid-rework FERAL §7 (5,1): Heart of the Wild bear form boost, cast by the shapeshift UnitScript - eff0 Stamina % (BP0 = HotW eff1), new eff1 AP % (BP1 = HotW eff1 + Feral Aggression eff1). Both BP-driven (ppl 0).',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx4': 2097152, 'ShapeshiftMask': 144, 'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0},
)


heart_of_the_wild_cat_effect_24900 = spell(
    id=24900,
    name='Heart of the Wild Cat Effect',
    school=School.NORMAL,
    attributes=400,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MOD_ATTACK_POWER_PCT),
    ],
    spell_icon_id=0,
    notes='druid-rework FERAL §7 (5,1): Heart of the Wild cat form boost, cast by the shapeshift UnitScript - eff0 AP % -> HASTE_ALL (BP0 = HotW eff1), new eff1 AP % (BP1 = Feral Aggression eff1). Both BP-driven (ppl 0).',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx4': 2097152, 'ShapeshiftMask': 1, 'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0},
)


feral_swiftness_passive_1a_24867 = spell(
    id=24867,
    name='Feral Swiftness Passive 1a',
    school=School.NORMAL,
    attributes=128,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MOD_INCREASE_SPEED),
    ],
    spell_icon_id=67,
    notes='druid-rework FERAL §7 (2,0): Feral Swiftness form boost, cast by the shapeshift UnitScript - eff0 dodge -> MOD_INCREASE_SPEED, BP-driven (cat 10/20, bear half); cat/bear/dire bear ShapeshiftMask kept.',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx4': 2097152, 'ShapeshiftMask': SS_FERAL, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 8, 'SpellLevel': 8, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'Increases movement speed.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement speed increased.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 7, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


survival_of_the_fittest_62069 = spell(
    id=62069,
    name='Elder Hide',
    school=School.NORMAL,
    attributes=400,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.MOD_BASE_RESISTANCE_PCT, misc_value=1),
    ],
    spell_icon_id=1558,
    notes='druid-rework FERAL §7 (0,1): renamed Elder Hide - the bear item-armor boost, cast by the shapeshift UnitScript with BP0 = Elder Hide eff1 (10/20/30); both bears (Stances drop it on the next form change).',
    raw_overrides={'ShapeshiftMask': SS_ANY_BEAR, 'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Increases your Armor contribution from cloth and leather items while in Bear Form or Dire Bear Form.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


savage_defense_62606 = spell(
    id=62606,
    name='Savage Defense',
    school=School.NATURE,
    attributes=262144,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.SCHOOL_ABSORB, misc_value=127),
    ],
    spell_icon_id=2323,
    notes="druid-rework FERAL §7 (6,0) + §0.16 Q13: a plain all-schools absorb pool, BP-driven by spell_dru_savage_defense_talent (existing remaining absorb + % of armor); ProcTypeMask/ProcCharges dropped (the stock spell_proc row's ProcFlags 0 now resolves to 0 - never procs); stock spell_dru_savage_defense unbound; ShapeshiftMask 0x80 so entering Bestial Fury drops it. Icon matches its own talent (2323, was the stock 146 which collided with Primal Fury 801 - talent-tooltip-audit finding).",
    raw_overrides={'ShapeshiftMask': SS_BEAR, 'CastingTimeIndex': 1, 'ProcChance': 100, 'BaseLevel': 1, 'SpellLevel': 1, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 14198, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Absorbs damage from all schools. Lasts $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Absorbs damage from all schools.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 7, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_2': 1.0},
)


natural_reaction_57893 = spell(
    id=57893,
    name='Natural Reaction',
    school=School.NORMAL,
    dispel=DispelType.MAGIC,
    attributes=134217728,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=EffectType.ENERGIZE, base_points=49, implicit_target_a=1, misc_value=1),
    ],
    spell_icon_id=2862,
    notes="druid-rework FERAL §7 (5,0): Natural Reaction's rage-on-dodge energize retuned to 5/10/15 rage.",
    raw_overrides={'AttributesEx2': 4, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 60, 'SpellLevel': 60, 'DurationIndex': 0, 'EquippedItemClass': -1, 'SpellVisualID_1': 12490, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Generates $/10;s1 rage.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


natural_reaction_59071 = spell(
    id=59071,
    name='Natural Reaction',
    school=School.NORMAL,
    dispel=DispelType.MAGIC,
    attributes=134217728,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=EffectType.ENERGIZE, base_points=99, implicit_target_a=1, misc_value=1),
    ],
    spell_icon_id=2862,
    notes="druid-rework FERAL §7 (5,0): Natural Reaction's rage-on-dodge energize retuned to 5/10/15 rage.",
    raw_overrides={'AttributesEx2': 4, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 60, 'SpellLevel': 60, 'DurationIndex': 0, 'EquippedItemClass': -1, 'SpellVisualID_1': 12490, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Generates $/10;s1 rage.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


natural_reaction_59072 = spell(
    id=59072,
    name='Natural Reaction',
    school=School.NORMAL,
    dispel=DispelType.MAGIC,
    attributes=134217728,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=EffectType.ENERGIZE, base_points=149, implicit_target_a=1, misc_value=1),
    ],
    spell_icon_id=2862,
    notes="druid-rework FERAL §7 (5,0): Natural Reaction's rage-on-dodge energize retuned to 5/10/15 rage.",
    raw_overrides={'AttributesEx2': 4, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 60, 'SpellLevel': 60, 'DurationIndex': 0, 'EquippedItemClass': -1, 'SpellVisualID_1': 12490, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Generates $/10;s1 rage.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


infected_wounds_58180 = spell(
    id=58180,
    name='Infected Wounds',
    school=School.NATURE,
    dispel=DispelType.DISEASE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=12000,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=-15, mechanic=8, implicit_target_a=6, apply_aura=AuraType.MOD_MELEE_HASTE),
    ],
    spell_icon_id=2857,
    notes="druid-rework FERAL §7 (7,3): Infected Wounds' Mangle slow - eff0 movement snare removed, eff1 attack speed -7/-14/-20% flat (ppl 0); cast by spell_dru_mangle for the caster's rank.",
    raw_overrides={'AttributesEx': 131208, 'AttributesEx2': 16777216, 'AttributesEx3': 131072, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 50, 'SpellLevel': 50, 'RangeIndex': 2, 'CumulativeAura': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 11569, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': "Your Mangle reduces the target's attack speed by $58180s2% for $58180d.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Attack speed slowed by $s2%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 7, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'NameSubtext_Lang_enUS': ''},
)


infected_wounds_58181 = spell(
    id=58181,
    name='Infected Wounds',
    school=School.NATURE,
    dispel=DispelType.DISEASE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=12000,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=-21, mechanic=8, implicit_target_a=6, apply_aura=AuraType.MOD_MELEE_HASTE),
    ],
    spell_icon_id=2857,
    notes="druid-rework FERAL §7 (7,3): Infected Wounds' Mangle slow - eff0 movement snare removed, eff1 attack speed -7/-14/-20% flat (ppl 0); cast by spell_dru_mangle for the caster's rank.",
    raw_overrides={'AttributesEx': 131208, 'AttributesEx3': 131072, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 50, 'SpellLevel': 50, 'RangeIndex': 2, 'CumulativeAura': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 11569, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': "Your Mangle reduces the target's attack speed by $58181s2% for $58181d.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Attack speed slowed by $s2%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 7, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'NameSubtext_Lang_enUS': ''},
)


bear_form_passive_1178 = spell(
    id=1178,
    name='Bear Form (Passive)',
    school=School.NATURE,
    attributes=80,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=369, implicit_target_a=1, apply_aura=AuraType.MOD_BASE_RESISTANCE_PCT, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=29, points_per_level=3.0, implicit_target_a=1, apply_aura=AuraType.MOD_ATTACK_POWER),
    ],
    spell_icon_id=107,
    notes='druid-rework FERAL §0.16 / CORE-AUDIT row 37 + user decision 2026-09-24: the form-5 (Bestial Fury) passive, an identical copy of the Dire Bear passive 9635 (effects, values, BaseLevel/SpellLevel 10, no MaxLevel) so Bestial Fury keeps every bear passive; keeps its own ShapeshiftMask 16. Stock spell_dru_bear_form_passive unbound.',
    raw_overrides={'ShapeshiftMask': SS_BESTIAL_FURY, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 10, 'SpellLevel': 10, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Passive', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712188, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 7, 'SpellClassMask_3': 2, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


dire_bear_form_passive_9635 = spell(
    id=9635,
    name='Dire Bear Form (Passive)',
    school=School.NATURE,
    attributes=80,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=369, implicit_target_a=1, apply_aura=AuraType.MOD_BASE_RESISTANCE_PCT, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=29, points_per_level=3.0, implicit_target_a=1, apply_aura=AuraType.MOD_ATTACK_POWER),
    ],
    spell_icon_id=107,
    notes="druid-rework FERAL §0.16 / CORE-AUDIT row 37 + user decision 2026-09-24: the form-8 passive is the everyday bear's at every level now, so it scales from level 10 - BaseLevel = SpellLevel = 10, no MaxLevel, eff2 attack power 30 + 3/level (stock Bear Form's values below 40, stock Dire Bear's from 40 on: 120 at 40, 240 at 80); eff0 armor contribution +370% and eff1 Stamina +25% flat at every level. Stock spell_dru_bear_form_passive unbound.",
    raw_overrides={'ShapeshiftMask': SS_BEAR, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 10, 'SpellLevel': 10, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Passive', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712188, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 7, 'SpellClassMask_3': 2, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


improved_barkskin_passive_66530 = spell(
    id=66530,
    name='Improved Barkskin (Passive)',
    school=School.NATURE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MOD_BASE_RESISTANCE_PCT, misc_value=1),
    ],
    spell_icon_id=107,
    notes='druid-rework FERAL §0.2 / PLAN §4.4: orphaned Improved Barkskin passive - dword 3 bit 0x20000 reclaimed for Upheaval (200422), only BEAR_FORM_PASSIVE left on it.',
    raw_overrides={'AttributesEx2': 524288, 'ShapeshiftMask': 4, 'ShapeshiftExclude': 1073741843, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 10, 'SpellLevel': 10, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectDieSides_2': 1, 'EffectDieSides_3': 1, 'EffectBasePoints_2': -1, 'EffectBasePoints_3': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Passive', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712188, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 7, 'SpellClassMask_3': BEAR_FORM_PASSIVE, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


# ============================================================================
# druid-rework FERAL WP-A: new trigger/buff spells (FERAL §2/§4/§7 with §0.16, WP-BRIEF §3). None of
# them carries a family bit (FERAL §3a: no SpellMod or charge consumption may reach them). "BP-driven"
# effects get their real value from CastCustomSpell in spell_druid_feral.cpp, so they have no level
# scaling and their stored base point is only a placeholder.
# ============================================================================


def _feral_raw(desc, aura_desc=None, **extra):
    raw = {
        'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 7, 'EquippedItemClass': -1,
        'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '',
        'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': desc,
        'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0,
    }
    if aura_desc is not None:
        raw['AuraDescription_Lang_Mask'] = 16712190
        raw['AuraDescription_Lang_enUS'] = aura_desc
    raw.update(extra)
    return raw


def _feral_buff_kwargs(duration_ms, attributes=0):
    return dict(school=School.NORMAL, attributes=attributes, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
                mana_cost=0, mana_cost_pct=0, range_yards=0.0, duration_ms=duration_ms)


# SPELL_ATTR0_DO_NOT_DISPLAY | SPELL_ATTR0_DO_NOT_LOG - hidden helper auras.
_HIDDEN_AURA_ATTRIBUTES = 0x80 | 0x100
# SPELL_ATTR3_NOT_A_PROC (SharedDefines.h): lets a triggered spell trigger other auras' procs
# (SpellAuras.cpp Aura::IsProcTriggeredOnEvent).
_SPELL_ATTR3_NOT_A_PROC = 0x00000200


tooth_and_claw_200438 = spell(
    id=200438, name='Tooth and Claw', **_feral_buff_kwargs(8000),
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2229,
    notes="NEW (docs/reworks/druid-feral-addition.md §2, FERAL-ADDENDUM §3.1): proc buff, up to 2 charges, granted "
          "by Mangle (Bear) and Maul while Bestial Fury is active (Druid::TryGrantToothAndClaw), and by Pulverize/"
          "Upheaval via Predatory Strikes' bear clause (Druid::OnSwellSpent). Enables Savage Bite 200439. "
          "ShapeshiftMask 0x10 (Bestial Fury/form 5 only, same as Swell 200426) - leaving Bestial Fury drops it with "
          "no script needed. CumulativeAura 2: a proc at 0-1 charges adds 1 and refreshes to 8 sec; a proc at 2 "
          "refreshes only (stock behaviour, addendum pending item 2). No family bit. Icon shared with Bestial Fury "
          "2229 (no icon mined this pass).",
    raw_overrides=_feral_raw(
        "A proc buff.  Enables Savage Bite.  Stacks up to 2 times, refreshing $d each time.  Removed when Bestial "
        "Fury ends.",
        "Enables Savage Bite.",
        CumulativeAura=2, ShapeshiftMask=SS_BESTIAL_FURY,
    ),
)


swell_200426 = spell(
    id=200426, name='Swell', **_feral_buff_kwargs(20000),
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.MOD_SCALE),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2005,
    notes="NEW (druid-rework FERAL §4 'Swell', WP-BRIEF §3/§4 item 6): +2% physical damage and +5% size per stack, 5 "
          "stacks; ShapeshiftMask 0x10 = Bestial Fury only, so leaving Bestial Fury drops it. Every source goes through "
          "Druid::AddSwell (15 sec in combat / 20 sec out, reset on gain); spell_dru_swell drops one stack on expiry.",
    raw_overrides=_feral_raw(
        "Increases your physical damage done by $s1% and your size by $s2% per stack.  Stacks up to $u times.  Lasts "
        "15 sec in combat and $d out of combat; each new stack resets the duration, and when it expires one stack is "
        "removed.",
        "Physical damage done increased by $s1% per stack.",
        CumulativeAura=5, ShapeshiftMask=SS_BESTIAL_FURY,
    ),
)
scripted_by(swell_200426, 'spell_dru_swell')


infected_wound_200427 = spell(
    id=200427,
    name='Infected Wound',
    school=School.NATURE,
    dispel=DispelType.DISEASE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=4000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=26, points_per_level=5.105, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=1000),
    ],
    spell_icon_id=2857,
    notes="NEW (druid-rework FERAL §11.3 with §0.16 Q9, WP-BRIEF §3): Infected Wounds' proc - one full Rake (the "
          "level-24 Rake hit + 3 ticks = 107 -> 4 ticks of ~27, ppl = Rake's (2.839 + 3 x 5.857)/4 = 5.105; stored 26 "
          "-> 27 at level 24, ~313 per tick at 80) over 4 sec as 4 Nature ticks, +0.0475 AP per tick (0.19 total). "
          "Disease, melee DefenseType, no bleed mechanic (excluded from Primal Gore's Mastery), no family bit. Icon "
          "2857 like the talent (note: spell_gen_black_magic_enchant's stock icon-2857 check lets it proc Black Magic, "
          "the same as the stock Infected Wounds slow).",
    raw_overrides=_feral_raw(
        "Deals $o1 Nature damage over $d.",
        "Taking $s1 Nature damage every $t1 sec.",
        BaseLevel=24, SpellLevel=24, MaxLevel=80, DefenseType=2, RangeIndex=13,
    ),
)
bonus_coefficients(infected_wound_200427, ap_dot=0.0475)


shredded_defense_200428 = spell(
    id=200428,
    name='Shredded Defense',
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=6, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=565,
    notes="NEW (druid-rework FERAL §7 (3,0) capstone, WP-BRIEF §3): +5% Physical damage taken from the caster per "
          "stack, 3 stacks, 6 sec, per caster (§13 Q8); read by the Druid damage hooks. Cast by "
          "spell_dru_shredding_attacks from behind. No family bit.",
    raw_overrides=_feral_raw(
        "Increases the Physical damage the target takes from the caster by $s1% per stack for $d.  Stacks up to $u "
        "times.",
        "Physical damage taken from the caster increased by $s1% per stack.",
        CumulativeAura=3, RangeIndex=13,
    ),
)


fury_swipe_200429 = spell(
    id=200429,
    name='Fury Swipe',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, base_points=309, implicit_target_a=6),
        Effect(type=EffectType.ENERGIZE, base_points=199, implicit_target_a=1, misc_value=1),
    ],
    spell_icon_id=4114,
    notes="NEW (druid-rework FERAL §7 (4,1), WP-BRIEF §3): 310% weapon damage, non-normalized (uses the actual "
          "swing); eff1 +20 rage, prevented outside bear by spell_dru_fury_swipe. Physical, melee DefenseType. "
          "AttributesEx3 SPELL_ATTR3_NOT_A_PROC implements §13 Q7's default ('can crit, triggers Primal Fury and "
          "Savage Defense'): without it a proc-triggered spell can't trigger other auras. No family bit. Visual: "
          "Swipe (Bear)'s.",
    raw_overrides=_feral_raw(
        "Deals $s1% weapon damage.  In Bear Form, also generates $/10;s2 rage.",
        DefenseType=2, PreventionType=2, RangeIndex=2, AttributesEx3=_SPELL_ATTR3_NOT_A_PROC, SpellVisualID_1=189,
        EffectBonusMultiplier_1=1.0, DurationIndex=0,
    ),
)
scripted_by(fury_swipe_200429, 'spell_dru_fury_swipe')


nurturing_instinct_empower_200430 = spell(
    id=200430, name='Nurturing Instinct', **_feral_buff_kwargs(15000),
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=2254,
    notes="NEW (druid-rework FERAL §7 (4,3), WP-BRIEF §3): 15 sec, 2 charges consumed by any feral damage ability "
          "(§13 Q17); both SpellMods BP-driven (BP0 = BP1 = Nurturing Instinct eff1, 15/30) by "
          "spell_dru_nurturing_instinct_empower.",
    raw_overrides=_feral_raw(
        "Your next $n melee abilities deal increased damage.",
        "Your next melee abilities deal increased damage.",
        ProcCharges=2,
        EffectSpellClassMaskA_1=NURTURING_INSTINCT_DAMAGE[0], EffectSpellClassMaskA_2=NURTURING_INSTINCT_DAMAGE[1],
        EffectSpellClassMaskA_3=NURTURING_INSTINCT_DAMAGE[2],
        EffectSpellClassMaskB_1=NURTURING_INSTINCT_DOT[0], EffectSpellClassMaskB_2=NURTURING_INSTINCT_DOT[1],
        EffectSpellClassMaskB_3=NURTURING_INSTINCT_DOT[2],
    ),
)


feral_instinct_buff_200431 = spell(
    id=200431, name='Feral Instinct', **_feral_buff_kwargs(6000),
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=127),
    ],
    spell_icon_id=103,
    notes="NEW (druid-rework FERAL §7 (1,0), WP-BRIEF §3): Tiger's Fury companion, all damage +1/2/3% (BP-driven from "
          "Feral Instinct eff0; spell_dru_tiger_s_fury_feral matches Tiger's Fury's duration).",
    raw_overrides=_feral_raw("Increases all damage you deal.", "All damage dealt increased."),
)


king_of_the_jungle_energy_200432 = spell(
    id=200432, name='King of the Jungle', **_feral_buff_kwargs(10000),
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.PERIODIC_ENERGIZE, amplitude=1000, misc_value=3),
    ],
    spell_icon_id=2850,
    notes="NEW (druid-rework FERAL §7 (8,0), WP-BRIEF §3): energy over 10 sec after Tiger's Fury - BP-driven energy per "
          "tick (King of the Jungle eff1 / 10: 2/4/6 per sec = 20/40/60 total).",
    raw_overrides=_feral_raw("Restores energy over $d.", "Restoring energy."),
)


stampede_bear_200433 = spell(
    id=200433, name='Stampede', **_feral_buff_kwargs(10000),
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COST),
    ],
    spell_icon_id=1559,
    notes="NEW (druid-rework FERAL §7 (2,0) capstone, WP-BRIEF §3): cast by spell_dru_feral_charge after Feral Charge "
          "(Bear) with Feral Swiftness r2 - next Mangle (Bear) costs no rage (1 charge, 10 sec, §13 Q19); the cooldown "
          "reset is the script's.",
    raw_overrides=_feral_raw(
        "Your next Mangle (Bear) costs no rage.", "Your next Mangle (Bear) costs no rage.",
        ProcCharges=1, EffectSpellClassMaskA_2=MANGLE_BEAR,
    ),
)


stampede_cat_200434 = spell(
    id=200434, name='Stampede', **_feral_buff_kwargs(10000),
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COST),
    ],
    spell_icon_id=3930,
    notes="NEW (druid-rework FERAL §7 (2,0) capstone, WP-BRIEF §3): cast by spell_dru_feral_charge after Feral Charge "
          "(Cat) with Feral Swiftness r2 - next Ravage costs no energy (1 charge, 10 sec); the no-stealth part is "
          "spell_dru_ravage (CheckCast) which also removes this aura after the cast.",
    raw_overrides=_feral_raw(
        "Your next Ravage costs no energy and does not require stealth.",
        "Your next Ravage costs no energy and does not require stealth.",
        ProcCharges=1, EffectSpellClassMaskA_1=RAVAGE,
    ),
)


improved_mangle_rage_200435 = spell(
    id=200435, name='Improved Mangle', **_feral_buff_kwargs(None),
    effects=[
        Effect(type=EffectType.ENERGIZE, base_points=149, implicit_target_a=1, misc_value=1),
    ],
    spell_icon_id=2312,
    notes="NEW (druid-rework FERAL §7 (8,2) capstone, WP-BRIEF §3): +15 rage, cast by spell_dru_mangle (Mangle (Bear), "
          "25% x (1 + Proc Chance)).",
    raw_overrides=_feral_raw("Generates $/10;s1 rage.", DurationIndex=0),
)


rend_and_tear_crit_200436 = spell(
    id=200436, name='Rend and Tear', **_feral_buff_kwargs(10000, attributes=_HIDDEN_AURA_ATTRIBUTES),
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CRITICAL_CHANCE),
    ],
    spell_icon_id=494,
    notes="NEW (druid-rework CORE-AUDIT row 24, WP-BRIEF §3): hidden 1-charge crit helper - the CanPrepare hook casts it "
          "with BP0 = Rend and Tear eff1 before a Ferocious Bite on a target with the caster's Rip or Lacerate, and "
          "removes it on any other Ferocious Bite/Rip prepare (Rip shares dword 1 0x800000).",
    raw_overrides=_feral_raw("Ferocious Bite critical strike chance increased.", ProcCharges=1,
                             EffectSpellClassMaskA_1=RIP_FEROCIOUS_BITE),
)


bestial_fury_rage_200437 = spell(
    id=200437, name='Bestial Fury', **_feral_buff_kwargs(-1, attributes=_HIDDEN_AURA_ATTRIBUTES),
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=AuraType.MOD_RAGE_FROM_DAMAGE_DEALT),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=17),
    ],
    spell_icon_id=2229,
    notes="NEW (druid-rework FERAL §0.16 + WP-BRIEF §4 item 2): hidden aura linked to Bestial Fury 200425 "
          "(linked_spell type 2, druid_talents.py) - +50% rage from damage dealt (Unit::RewardRage) and the Polymorph "
          "immunity Bear Form 5487's own eff1 gives (Bestial Fury replaces that aura).",
    raw_overrides=_feral_raw("Rage from damage dealt increased by $s1%.  Immune to Polymorph effects."),
)


# ============================================================================
# druid-rework FERAL WP-A: new talent ranks (FERAL §7, WP-BRIEF §3). "DUMMY" values the C++ reads are
# APPLY_AURA + DUMMY (a plain SPELL_EFFECT_DUMMY creates no AuraEffect for GetRankAmount to find - Resto
# code-review lesson). Capstones follow PLAN §2 (every rank carries the clause; grey below max).
# None of these carries a ShapeshiftMask except Fury Swipes (145) and Savage Defense (0x80) (WP-BRIEF §3).
# ============================================================================


def _cap_lower(rank_text, clause):
    return f"{rank_text}\n\n|cFF9D9D9DCapstone Bonus: {clause}|r"


def _cap_final(rank_text, clause):
    return f"{rank_text}\n\nCapstone Bonus: {clause}"


def _feral_talent_raw(desc, **extra):
    return _feral_raw(desc, AuraDescription_Lang_Mask=16712188, EffectBonusMultiplier_1=1.0, **extra)


def _aura(aura, base_points, misc_value=0, **kwargs):
    return Effect(type=EffectType.APPLY_AURA, base_points=base_points, implicit_target_a=1, apply_aura=aura,
                  misc_value=misc_value, **kwargs)


# (0,1) Elder Hide - talent 794 (was Thick Hide), capstone r3
_ELDER_HIDE_TEXT = ("Increases your Stamina by $s1%.  Increases the Armor contribution from cloth and leather items while "
                    "in Bear Form or Dire Bear Form by $s2%.")
_ELDER_HIDE_CLAUSE = ("Your Ironfur increases the healing you receive from other players by $200442s3% per stack.")
_ELDER_HIDE_NOTES = ("NEW (druid-rework FERAL §7 (0,1), WP-BRIEF §3), talent 794 (was Thick Hide): eff0 Stamina "
                     "1/2/3%; eff1 DUMMY 10/20/30 = bear item-armor % (form-boost BP0 of 62069 'Elder Hide'); r3 eff2 "
                     "DUMMY 4 = healing received from other players per Ironfur stack (healing hook).")
elder_hide_200440 = spell(
    id=200440, name='Elder Hide', **_dru_passive_talent_kwargs(),
    effects=[_aura(AuraType.MOD_TOTAL_STAT_PERCENTAGE, 0, 2), _aura(AuraType.DUMMY, 9)],
    spell_icon_id=1558, notes=_ELDER_HIDE_NOTES + " Rank 1/3.",
    raw_overrides=_feral_talent_raw(_cap_lower(_ELDER_HIDE_TEXT, _ELDER_HIDE_CLAUSE)),
)
elder_hide_200441 = spell(
    id=200441, name='Elder Hide', **_dru_passive_talent_kwargs(),
    effects=[_aura(AuraType.MOD_TOTAL_STAT_PERCENTAGE, 1, 2), _aura(AuraType.DUMMY, 19)],
    spell_icon_id=1558, notes=_ELDER_HIDE_NOTES + " Rank 2/3.",
    raw_overrides=_feral_talent_raw(_cap_lower(_ELDER_HIDE_TEXT, _ELDER_HIDE_CLAUSE)),
)
elder_hide_200442 = spell(
    id=200442, name='Elder Hide', **_dru_passive_talent_kwargs(),
    effects=[_aura(AuraType.MOD_TOTAL_STAT_PERCENTAGE, 2, 2), _aura(AuraType.DUMMY, 29), _aura(AuraType.DUMMY, 3)],
    spell_icon_id=1558, notes=_ELDER_HIDE_NOTES + " Rank 3/3 (capstone).",
    raw_overrides=_feral_talent_raw(_cap_final(_ELDER_HIDE_TEXT, _ELDER_HIDE_CLAUSE)),
)


# (0,2) Primal Attunement - minted talent 60040
_PRIMAL_ATTUNEMENT_NOTES = ("NEW (druid-rework FERAL §7 (0,2) + §13 Q6), talent 60040: percentage Mastery "
                            "(MOD_CUSTOM_STAT_PCT misc 1<<CR_MASTERY) +2/4/6.")
primal_attunement_200443 = spell(
    id=200443, name='Primal Attunement', **_dru_passive_talent_kwargs(),
    effects=[_aura(AuraType.MOD_CUSTOM_STAT_PCT, 1, 1 << CombatRating.MASTERY)],
    spell_icon_id=2025, notes=_PRIMAL_ATTUNEMENT_NOTES + " Rank 1/3.",
    raw_overrides=_feral_talent_raw("Increases your Mastery by $s1%."),
)
primal_attunement_200444 = spell(
    id=200444, name='Primal Attunement', **_dru_passive_talent_kwargs(),
    effects=[_aura(AuraType.MOD_CUSTOM_STAT_PCT, 3, 1 << CombatRating.MASTERY)],
    spell_icon_id=2025, notes=_PRIMAL_ATTUNEMENT_NOTES + " Rank 2/3.",
    raw_overrides=_feral_talent_raw("Increases your Mastery by $s1%."),
)
primal_attunement_200445 = spell(
    id=200445, name='Primal Attunement', **_dru_passive_talent_kwargs(),
    effects=[_aura(AuraType.MOD_CUSTOM_STAT_PCT, 5, 1 << CombatRating.MASTERY)],
    spell_icon_id=2025, notes=_PRIMAL_ATTUNEMENT_NOTES + " Rank 3/3.",
    raw_overrides=_feral_talent_raw("Increases your Mastery by $s1%."),
)


# (1,2) Flesh Render - minted talent 60041
_FLESH_RENDER_TEXT = ("Increases the damage of your Lacerate by $s1%.  Your Lacerate has a $s3% chance to apply an "
                      "additional application.")
_FLESH_RENDER_NOTES = ("NEW (druid-rework FERAL §7 (1,2), WP-BRIEF §3), talent 60041: +10/20/30% Lacerate hit (DAMAGE) "
                       "and bleed (DOT); eff2 DUMMY 10/20/30 = extra-application chance (spell_dru_lacerate, x (1 + "
                       "Proc Chance)).")
flesh_render_200446 = spell(
    id=200446, name='Flesh Render', **_dru_passive_talent_kwargs(),
    effects=[
        _aura(AuraType.ADD_PCT_MODIFIER, 9, SpellModOp.DAMAGE),
        _aura(AuraType.ADD_PCT_MODIFIER, 9, SpellModOp.DOT),
        _aura(AuraType.DUMMY, 9),
    ],
    spell_icon_id=3777, notes=_FLESH_RENDER_NOTES + " Rank 1/3.",
    raw_overrides=_feral_talent_raw(_FLESH_RENDER_TEXT, EffectSpellClassMaskA_2=LACERATE, EffectSpellClassMaskB_2=LACERATE),
)
flesh_render_200447 = spell(
    id=200447, name='Flesh Render', **_dru_passive_talent_kwargs(),
    effects=[
        _aura(AuraType.ADD_PCT_MODIFIER, 19, SpellModOp.DAMAGE),
        _aura(AuraType.ADD_PCT_MODIFIER, 19, SpellModOp.DOT),
        _aura(AuraType.DUMMY, 19),
    ],
    spell_icon_id=3777, notes=_FLESH_RENDER_NOTES + " Rank 2/3.",
    raw_overrides=_feral_talent_raw(_FLESH_RENDER_TEXT, EffectSpellClassMaskA_2=LACERATE, EffectSpellClassMaskB_2=LACERATE),
)
flesh_render_200448 = spell(
    id=200448, name='Flesh Render', **_dru_passive_talent_kwargs(),
    effects=[
        _aura(AuraType.ADD_PCT_MODIFIER, 29, SpellModOp.DAMAGE),
        _aura(AuraType.ADD_PCT_MODIFIER, 29, SpellModOp.DOT),
        _aura(AuraType.DUMMY, 29),
    ],
    spell_icon_id=3777, notes=_FLESH_RENDER_NOTES + " Rank 3/3.",
    raw_overrides=_feral_talent_raw(_FLESH_RENDER_TEXT, EffectSpellClassMaskA_2=LACERATE, EffectSpellClassMaskB_2=LACERATE),
)


# (4,0) Rending Swipes - minted talent 60042
_RENDING_SWIPES_TEXT = ("Increases the damage of your Thrash and Swipe by $s1%.  Targets affected by your Thrash bleed take "
                        "$s3% increased damage from your Swipe and Upheaval.")
_RENDING_SWIPES_NOTES = ("NEW (druid-rework FERAL §7 (4,0), WP-BRIEF §3), talent 60042: +10/20% Thrash (hit and bleed) "
                         "and Swipe (Bear/Cat) damage; eff2 DUMMY 5/10 = bonus for Swipe (Bear/Cat) and Upheaval vs "
                         "targets with the caster's Thrash (Druid damage hooks).")

rending_swipes_200449 = spell(
    id=200449, name='Rending Swipes', **_dru_passive_talent_kwargs(),
    effects=[
        _aura(AuraType.ADD_PCT_MODIFIER, 9, SpellModOp.DAMAGE),
        _aura(AuraType.ADD_PCT_MODIFIER, 9, SpellModOp.DOT),
        _aura(AuraType.DUMMY, 4),
    ],
    spell_icon_id=4001, notes=_RENDING_SWIPES_NOTES + " Rank 1/2.",
    raw_overrides=_feral_talent_raw(_RENDING_SWIPES_TEXT, EffectSpellClassMaskA_2=SWIPE_BEAR, EffectSpellClassMaskA_3=SWIPE_CAT | THRASH, EffectSpellClassMaskB_3=THRASH),
)

rending_swipes_200450 = spell(
    id=200450, name='Rending Swipes', **_dru_passive_talent_kwargs(),
    effects=[
        _aura(AuraType.ADD_PCT_MODIFIER, 19, SpellModOp.DAMAGE),
        _aura(AuraType.ADD_PCT_MODIFIER, 19, SpellModOp.DOT),
        _aura(AuraType.DUMMY, 9),
    ],
    spell_icon_id=4001, notes=_RENDING_SWIPES_NOTES + " Rank 2/2.",
    raw_overrides=_feral_talent_raw(_RENDING_SWIPES_TEXT, EffectSpellClassMaskA_2=SWIPE_BEAR, EffectSpellClassMaskA_3=SWIPE_CAT | THRASH, EffectSpellClassMaskB_3=THRASH),
)



# (4,1) Fury Swipes - minted talent 60043. The chance lives in procs_on (Proc Chance applies automatically,
# SpellAuras.cpp); raw ProcChance only feeds the tooltip's $h.
_FURY_SWIPES_TEXT = ("Your autoattacks in Cat Form or Bear Form have a $h% chance to cause a Fury Swipe, dealing "
                     "$200429s1% weapon damage.  In Bear Form, Fury Swipe also generates $/10;200429s2 rage.  Cannot "
                     "occur more than once every 3 sec.  Chance is modified by Proc Chance.")
_FURY_SWIPES_NOTES = ("NEW (druid-rework FERAL §7 (4,1), WP-BRIEF §3), talent 60043: autoattacks proc Fury Swipe 200429 "
                      "3/5/8% (3 sec ICD), cat/bear/dire bear only (ShapeshiftMask 145).")

fury_swipes_200451 = spell(
    id=200451, name='Fury Swipes', **_dru_passive_talent_kwargs(),
    effects=[
        _aura(AuraType.PROC_TRIGGER_SPELL, -1, trigger_spell=fury_swipe_200429.id),
    ],
    spell_icon_id=4114, notes=_FURY_SWIPES_NOTES + " Rank 1/3.",
    raw_overrides=_feral_talent_raw(_FURY_SWIPES_TEXT, ShapeshiftMask=SS_FERAL, ProcChance=3),
)

procs_on(fury_swipes_200451, proc_flags=PROC_FLAG_DONE_MELEE_AUTO_ATTACK,
         hit_mask=PROC_HIT_NORMAL | PROC_HIT_CRITICAL, chance=3, cooldown_ms=3000)

fury_swipes_200452 = spell(
    id=200452, name='Fury Swipes', **_dru_passive_talent_kwargs(),
    effects=[
        _aura(AuraType.PROC_TRIGGER_SPELL, -1, trigger_spell=fury_swipe_200429.id),
    ],
    spell_icon_id=4114, notes=_FURY_SWIPES_NOTES + " Rank 2/3.",
    raw_overrides=_feral_talent_raw(_FURY_SWIPES_TEXT, ShapeshiftMask=SS_FERAL, ProcChance=5),
)

procs_on(fury_swipes_200452, proc_flags=PROC_FLAG_DONE_MELEE_AUTO_ATTACK,
         hit_mask=PROC_HIT_NORMAL | PROC_HIT_CRITICAL, chance=5, cooldown_ms=3000)

fury_swipes_200453 = spell(
    id=200453, name='Fury Swipes', **_dru_passive_talent_kwargs(),
    effects=[
        _aura(AuraType.PROC_TRIGGER_SPELL, -1, trigger_spell=fury_swipe_200429.id),
    ],
    spell_icon_id=4114, notes=_FURY_SWIPES_NOTES + " Rank 3/3.",
    raw_overrides=_feral_talent_raw(_FURY_SWIPES_TEXT, ShapeshiftMask=SS_FERAL, ProcChance=8),
)

procs_on(fury_swipes_200453, proc_flags=PROC_FLAG_DONE_MELEE_AUTO_ATTACK,
         hit_mask=PROC_HIT_NORMAL | PROC_HIT_CRITICAL, chance=8, cooldown_ms=3000)



# (4,2) Bloodletting - minted talent 60044, capstone r2
_BLOODLETTING_TEXT = "Increases the damage of your Rip and Rake by $s1%."
_BLOODLETTING_CLAUSE = ("Your Rake reduces the cooldown of Tiger's Fury by $200455s3 sec.  Cannot occur more than once "
                        "every 3 sec.")
_BLOODLETTING_NOTES = ("NEW (druid-rework FERAL §7 (4,2), WP-BRIEF §3), talent 60044: +8/15% Rake hit (DAMAGE) and Rake/"
                       "Rip bleed (DOT, Rip via its Rip-only dword 3 bit).")

bloodletting_200454 = spell(
    id=200454, name='Bloodletting', **_dru_passive_talent_kwargs(),
    effects=[
        _aura(AuraType.ADD_PCT_MODIFIER, 7, SpellModOp.DAMAGE),
        _aura(AuraType.ADD_PCT_MODIFIER, 7, SpellModOp.DOT),
    ],
    spell_icon_id=90121, notes=_BLOODLETTING_NOTES + " Rank 1/2.",
    raw_overrides=_feral_talent_raw(_cap_lower(_BLOODLETTING_TEXT, _BLOODLETTING_CLAUSE), EffectSpellClassMaskA_1=RAKE, EffectSpellClassMaskB_1=RAKE, EffectSpellClassMaskB_3=RIP),
)

bloodletting_200455 = spell(
    id=200455, name='Bloodletting', **_dru_passive_talent_kwargs(),
    effects=[
        _aura(AuraType.ADD_PCT_MODIFIER, 14, SpellModOp.DAMAGE),
        _aura(AuraType.ADD_PCT_MODIFIER, 14, SpellModOp.DOT),
        _aura(AuraType.DUMMY, 2),
    ],
    spell_icon_id=90121, notes=_BLOODLETTING_NOTES + " Rank 2/2 (capstone): eff2 DUMMY 3 = seconds off Tiger's Fury per Rake (spell_dru_rake, 3 sec ICD).",
    raw_overrides=_feral_talent_raw(_cap_final(_BLOODLETTING_TEXT, _BLOODLETTING_CLAUSE), EffectSpellClassMaskA_1=RAKE, EffectSpellClassMaskB_1=RAKE, EffectSpellClassMaskB_3=RIP),
)



# (5,3) Bonebreaker - talent 797 (was Brutal Impact), capstone r3. CORE-AUDIT row 25 (C2 accepted): aura 163
# multiplies the whole 200% crit, so spell_dru_bonebreaker sets the amount to P/2 x Swell stacks (x (1 + 1.5 x
# Mastery%) with the capstone); the stored value is P = 14/27/40 points per stack.
_BONEBREAKER_TEXT = "Your Swell also increases your critical strike damage by $s1% per stack."
_BONEBREAKER_CLAUSE = "The critical strike damage per stack is increased by $200458s2% of your Mastery."
_BONEBREAKER_NOTES = ("NEW (druid-rework FERAL §7 (5,3) + §0.16 Q1/Q15, WP-BRIEF §3), talent 797: eff0 aura 163 misc 1 "
                      "(physical) P = 14/27/40 points per Swell stack, recalculated by spell_dru_bonebreaker on every "
                      "Swell change; every crit incl. periodic while Swell is up.")

bonebreaker_200456 = spell(
    id=200456, name='Bonebreaker', **_dru_passive_talent_kwargs(),
    effects=[
        _aura(AuraType.MOD_CRIT_DAMAGE_BONUS, 13, 1),
    ],
    spell_icon_id=599, notes=_BONEBREAKER_NOTES + " Rank 1/3.",
    raw_overrides=_feral_talent_raw(_cap_lower(_BONEBREAKER_TEXT, _BONEBREAKER_CLAUSE)),
)

bonebreaker_200457 = spell(
    id=200457, name='Bonebreaker', **_dru_passive_talent_kwargs(),
    effects=[
        _aura(AuraType.MOD_CRIT_DAMAGE_BONUS, 26, 1),
    ],
    spell_icon_id=599, notes=_BONEBREAKER_NOTES + " Rank 2/3.",
    raw_overrides=_feral_talent_raw(_cap_lower(_BONEBREAKER_TEXT, _BONEBREAKER_CLAUSE)),
)

bonebreaker_200458 = spell(
    id=200458, name='Bonebreaker', **_dru_passive_talent_kwargs(),
    effects=[
        _aura(AuraType.MOD_CRIT_DAMAGE_BONUS, 39, 1),
        _aura(AuraType.DUMMY, 149),
    ],
    spell_icon_id=599, notes=_BONEBREAKER_NOTES + " Rank 3/3 (capstone): eff1 DUMMY 150 = % of Mastery.",
    raw_overrides=_feral_talent_raw(_cap_final(_BONEBREAKER_TEXT, _BONEBREAKER_CLAUSE)),
)



# (6,0) Savage Defense - talent 1793 (was Primal Tenacity); the old passive 62600 is untrained in druid_talents.py.
_SAVAGE_DEFENSE_TEXT = ("Each time you land a direct damage critical strike while in Bear Form or Dire Bear Form, you add "
                        "an absorb equal to $s1% of your current armor to Savage Defense.  The pool lasts $62606d.  "
                        "Cannot occur more than once every 3 sec.  Does not function while Bestial Fury is active.  "
                        "Periodic damage does not trigger this effect.")
_SAVAGE_DEFENSE_NOTES = ("NEW (druid-rework FERAL §7 (6,0), WP-BRIEF §3), talent 1793: eff0 DUMMY 4/8 = % of current "
                         "armor added to the 62606 absorb pool (x2 during Berserk) by spell_dru_savage_defense_talent; "
                         "ShapeshiftMask 0x80 (everyday bear only - off in Bestial Fury). procs_on: direct melee crits, no "
                         "DONE_PERIODIC, 3 sec ICD.")

savage_defense_200459 = spell(
    id=200459, name='Savage Defense', **_dru_passive_talent_kwargs(),
    effects=[
        _aura(AuraType.DUMMY, 3),
    ],
    spell_icon_id=2323, notes=_SAVAGE_DEFENSE_NOTES + " Rank 1/2.",
    raw_overrides=_feral_talent_raw(_SAVAGE_DEFENSE_TEXT, ShapeshiftMask=SS_BEAR),
)

procs_on(savage_defense_200459, proc_flags=PROC_FLAG_DONE_MELEE_AUTO_ATTACK | PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS,
         spell_type_mask=PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=PROC_SPELL_PHASE_HIT,
         hit_mask=PROC_HIT_CRITICAL, chance=100, cooldown_ms=3000)

savage_defense_200460 = spell(
    id=200460, name='Savage Defense', **_dru_passive_talent_kwargs(),
    effects=[
        _aura(AuraType.DUMMY, 7),
    ],
    spell_icon_id=2323, notes=_SAVAGE_DEFENSE_NOTES + " Rank 2/2.",
    raw_overrides=_feral_talent_raw(_SAVAGE_DEFENSE_TEXT, ShapeshiftMask=SS_BEAR),
)

procs_on(savage_defense_200460, proc_flags=PROC_FLAG_DONE_MELEE_AUTO_ATTACK | PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS,
         spell_type_mask=PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=PROC_SPELL_PHASE_HIT,
         hit_mask=PROC_HIT_CRITICAL, chance=100, cooldown_ms=3000)



# (6,3) Sabertooth - talent 1798 (was Improved Leader of the Pack)
_SABERTOOTH_TEXT = ("Your Ferocious Bite extends the duration of your Rip on the target by $s1 sec, up to a maximum of 1.5 "
                    "times its original duration.")
_SABERTOOTH_NOTES = ("NEW (druid-rework FERAL §7 (6,3), WP-BRIEF §3), talent 1798: eff0 DUMMY 2/4/6 = seconds added to the "
                     "caster's Rip by spell_dru_ferocious_bite (cap 1.5 x the modded max duration, before the pro-rated "
                     "final tick).")

sabertooth_200461 = spell(
    id=200461, name='Sabertooth', **_dru_passive_talent_kwargs(),
    effects=[
        _aura(AuraType.DUMMY, 1),
    ],
    spell_icon_id=293, notes=_SABERTOOTH_NOTES + " Rank 1/3.",
    raw_overrides=_feral_talent_raw(_SABERTOOTH_TEXT),
)

sabertooth_200462 = spell(
    id=200462, name='Sabertooth', **_dru_passive_talent_kwargs(),
    effects=[
        _aura(AuraType.DUMMY, 3),
    ],
    spell_icon_id=293, notes=_SABERTOOTH_NOTES + " Rank 2/3.",
    raw_overrides=_feral_talent_raw(_SABERTOOTH_TEXT),
)

sabertooth_200463 = spell(
    id=200463, name='Sabertooth', **_dru_passive_talent_kwargs(),
    effects=[
        _aura(AuraType.DUMMY, 5),
    ],
    spell_icon_id=293, notes=_SABERTOOTH_NOTES + " Rank 3/3.",
    raw_overrides=_feral_talent_raw(_SABERTOOTH_TEXT),
)



# (8,3) Splintering Blows - talent 1796 (was Mangle). CORE-AUDIT row 23: a crit SpellMod on Pulverize's own bit,
# scaled by Swell stacks in spell_dru_splintering_blows (stored value = per-stack %). FERAL-ADDENDUM
# §3.3 (user decision): Savage Bite 200439 shares this same bit, so it reaches Savage Bite too with
# no extra mask - Savage Bite never consumes Swell, so it always reads the full current stack count.
_SPLINTERING_BLOWS_TEXT = ("Your Swell also increases the critical strike chance of your Pulverize and Savage Bite "
                           "by $s1% per stack.")
_SPLINTERING_BLOWS_NOTES = ("NEW (druid-rework FERAL §7 (8,3), WP-BRIEF §3), talent 1796: eff0 flat CRITICAL_CHANCE on "
                            "Pulverize (and Savage Bite, FERAL-ADDENDUM §3.3, sharing the PULVERIZE bit) 4/8/12 per "
                            "Swell stack (amount x stacks, recalculated on every Swell change).")

splintering_blows_200464 = spell(
    id=200464, name='Splintering Blows', **_dru_passive_talent_kwargs(),
    effects=[
        _aura(AuraType.ADD_FLAT_MODIFIER, 3, SpellModOp.CRITICAL_CHANCE),
    ],
    spell_icon_id=3998, notes=_SPLINTERING_BLOWS_NOTES + " Rank 1/3.",
    raw_overrides=_feral_talent_raw(_SPLINTERING_BLOWS_TEXT, EffectSpellClassMaskA_3=PULVERIZE),
)

splintering_blows_200465 = spell(
    id=200465, name='Splintering Blows', **_dru_passive_talent_kwargs(),
    effects=[
        _aura(AuraType.ADD_FLAT_MODIFIER, 7, SpellModOp.CRITICAL_CHANCE),
    ],
    spell_icon_id=3998, notes=_SPLINTERING_BLOWS_NOTES + " Rank 2/3.",
    raw_overrides=_feral_talent_raw(_SPLINTERING_BLOWS_TEXT, EffectSpellClassMaskA_3=PULVERIZE),
)

splintering_blows_200466 = spell(
    id=200466, name='Splintering Blows', **_dru_passive_talent_kwargs(),
    effects=[
        _aura(AuraType.ADD_FLAT_MODIFIER, 11, SpellModOp.CRITICAL_CHANCE),
    ],
    spell_icon_id=3998, notes=_SPLINTERING_BLOWS_NOTES + " Rank 3/3.",
    raw_overrides=_feral_talent_raw(_SPLINTERING_BLOWS_TEXT, EffectSpellClassMaskA_3=PULVERIZE),
)



# (9,0) Iron Hide - minted talent 60045
_IRON_HIDE_TEXT = ("Your Ironfur also reduces magic damage taken by $/10;s1% per stack.  Each cast of Ironfur reduces "
                   "the cooldown of Barkskin by 1 sec, no more than once every 1 sec.")
_IRON_HIDE_NOTES = ("NEW (druid-rework FERAL §7 (9,0), WP-BRIEF §3), talent 60045: eff0 DUMMY 6/12/20 = tenths of a "
                    "percent of magic damage reduction per Ironfur stack (Druid damage-taken hooks); spell_dru_ironfur "
                    "takes 1 sec off Barkskin per cast (1 sec ICD, Barkskin's 30 sec floor applies).")

iron_hide_200467 = spell(
    id=200467, name='Iron Hide', **_dru_passive_talent_kwargs(),
    effects=[
        _aura(AuraType.DUMMY, 5),
    ],
    spell_icon_id=2015, notes=_IRON_HIDE_NOTES + " Rank 1/3.",
    raw_overrides=_feral_talent_raw(_IRON_HIDE_TEXT),
)

iron_hide_200468 = spell(
    id=200468, name='Iron Hide', **_dru_passive_talent_kwargs(),
    effects=[
        _aura(AuraType.DUMMY, 11),
    ],
    spell_icon_id=2015, notes=_IRON_HIDE_NOTES + " Rank 2/3.",
    raw_overrides=_feral_talent_raw(_IRON_HIDE_TEXT),
)

iron_hide_200469 = spell(
    id=200469, name='Iron Hide', **_dru_passive_talent_kwargs(),
    effects=[
        _aura(AuraType.DUMMY, 19),
    ],
    spell_icon_id=2015, notes=_IRON_HIDE_NOTES + " Rank 3/3.",
    raw_overrides=_feral_talent_raw(_IRON_HIDE_TEXT),
)



# (9,2) Primal Gore ranks 2-3 (63503 is rank 1). CORE-AUDIT row 25 (C2): CRIT_DAMAGE_BONUS acts on the crit's
# extra damage, so +30/60/100% of it = x1.15/1.30/1.50 of a 200% crit.
_PRIMAL_GORE_TEXT = "Increases the critical strike damage of your bleeds by ${$m1/2}%."
_PRIMAL_GORE_CLAUSE = "While in Cat Form, your bleed damage is increased by $200471s2% of your Mastery."
_PRIMAL_GORE_NOTES = ("NEW (druid-rework FERAL §1/§7 (9,2), WP-BRIEF §3): Primal Gore grows 1 -> 3 ranks; eff0 "
                      "ADD_PCT_MODIFIER CRIT_DAMAGE_BONUS on the feral bleeds (Rake, Lacerate, Rip, Thrash).")

primal_gore_200470 = spell(
    id=200470, name='Primal Gore', **_dru_passive_talent_kwargs(),
    effects=[
        _aura(AuraType.ADD_PCT_MODIFIER, 59, SpellModOp.CRIT_DAMAGE_BONUS),
    ],
    spell_icon_id=262, notes=_PRIMAL_GORE_NOTES + " Rank 2/3 (+60% of the extra = x1.30).",
    raw_overrides=_feral_talent_raw(_cap_lower(_PRIMAL_GORE_TEXT, _PRIMAL_GORE_CLAUSE), EffectSpellClassMaskA_1=FERAL_BLEEDS[0], EffectSpellClassMaskA_2=FERAL_BLEEDS[1], EffectSpellClassMaskA_3=FERAL_BLEEDS[2]),
)

primal_gore_200471 = spell(
    id=200471, name='Primal Gore', **_dru_passive_talent_kwargs(),
    effects=[
        _aura(AuraType.ADD_PCT_MODIFIER, 99, SpellModOp.CRIT_DAMAGE_BONUS),
        _aura(AuraType.DUMMY, 99),
    ],
    spell_icon_id=262, notes=_PRIMAL_GORE_NOTES + " Rank 3/3 (capstone, +100% of the extra = x1.50): eff1 DUMMY 100 = % of Mastery added to cat-form bleed damage (Druid::ApplyDoneDamagePctMods).",
    raw_overrides=_feral_talent_raw(_cap_final(_PRIMAL_GORE_TEXT, _PRIMAL_GORE_CLAUSE), EffectSpellClassMaskA_1=FERAL_BLEEDS[0], EffectSpellClassMaskA_2=FERAL_BLEEDS[1], EffectSpellClassMaskA_3=FERAL_BLEEDS[2]),
)


# ---------------------------------------------------------------------------
# warlock-rework AFFLICTION pass - server-wide A1/A2 crit-damage exclusivity
# group (PLAN A1/A2, SHARED §1.1, AFFLICTION §4.8): druid's 3 of 27 hidden
# passives (Vengeance). Group 1201 itself and its rule are declared once, in
# the warlock DSL (warlock_trigger_spells.py).
# ---------------------------------------------------------------------------

def _crit_damage_passive_200695(spell_id, stored_bp):
    return spell(
        id=spell_id, name='Vengeance', school=School.SHADOW, attributes=464,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
        range_yards=RANGE_SELF, duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, base_points=stored_bp, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_DAMAGE_BONUS, misc_value=126)],
        spell_icon_id=47,
        notes='warlock-rework AFFLICTION §4.8 (A1/A2, SHARED §1.1): hidden crit-damage passive, no visible icon/tooltip; joins spell_group 1201 (rule 3, highest only, declared in the warlock DSL); linked (type=2) from its talent rank.',
        raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 7, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_Mask': 16712190, 'ProcChance': 101},
    )


vengeance_crit_200695 = _crit_damage_passive_200695(200695, 9)
vengeance_crit_200696 = _crit_damage_passive_200695(200696, 19)
vengeance_crit_200697 = _crit_damage_passive_200695(200697, 32)
