"""
Priest - player-castable spells (real cast_time_ms/cooldown_ms, not marked passive).

Split from a single source/classes/priest.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .priest_...` below) resolve.
"""

from lib.dsl import ApplyAura, AuraType, DispelType, Effect, EffectType, Mechanic, School, SpellModOp
from lib.dsl.registry import bonus_coefficients, scripted_by, skill_line_ability, spell, trained_by
from . import _masks
from .priest_trigger_spells import (
    angelic_feather_buff_200131,
    angelic_feather_place_200141,
    divine_hymn_64844,
    divine_star_pulse_200134,
    halo_pulse_200136,
    leap_of_faith_jump_200138,
    mind_sear_49821,
    prayer_of_mending_41635,
    void_eruption_buff_200140,
)


power_word_shield_17 = spell(
    id=17,
    name='Power Word: Shield',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    mechanic=19,
    attributes=329728,
    category=56,
    cast_time_ms=0,
    cooldown_ms=4000,
    category_cooldown_ms=4000,
    mana_cost=0,
    mana_cost_pct=23,
    range_yards=40.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=43, points_per_level=16.6296, implicit_target_a=21, apply_aura=AuraType.SCHOOL_ABSORB, misc_value=127),
    ],
    spell_icon_id=566,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 6); RealPointsPerLevel from rank1→level-60 slope (anchor rank 10901, rank 10); coefficient/cast_time_ms/mana_cost_pct from max rank (48066, rank 14); MaxLevel set to 80. '
          'Discipline rework baseline edit (docs/reworks/priest-disc-rework.md, "Baseline Changes"): cooldown_ms=4000 added alongside the stock 4-second category cooldown, so the spec\'s "4 sec base cooldown, reduced to 0 by Soul Warding (4,2) at full rank" holds. Soul Warding\'s SPELLMOD_COOLDOWN applies to BOTH RecoveryTime and CategoryRecoveryTime (Player::AddSpellAndCategoryCooldowns, Player.cpp:11181/11185), so -4 sec at rank 2 zeroes both.',
    raw_overrides={'AttributesEx2': 2621440, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Absorbs damage.', 'BaseLevel': 6, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Draws on the soul of the friendly target to shield them, absorbing $s1 damage.  Lasts $d.  While the shield holds, spellcasting will not be interrupted by damage.  Once shielded, the target cannot be shielded again for $6788d.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ExcludeTargetAuraSpell': 6788, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 1, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 6, 'SpellPriority': 50, 'SpellVisualID_1': 784, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


renew_139 = spell(
    id=139,
    name='Renew',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=17,
    range_yards=40.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=8, points_per_level=3.5577, implicit_target_a=21, apply_aura=AuraType.PERIODIC_HEAL, amplitude=3000),
    ],
    spell_icon_id=321,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 8); RealPointsPerLevel from rank1→level-60 slope (anchor rank 25315, rank 10); coefficient/cast_time_ms/mana_cost_pct from max rank (48068, rank 14); MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx3': 128, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Healing $s1 damage every $t1 seconds.', 'BaseLevel': 8, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals the target for $<total> over $d.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 0.37599998712539673, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_1': 64, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellDescriptionVariableID': 30, 'SpellLevel': 8, 'SpellPriority': 50, 'SpellVisualID_1': 280, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


mind_soothe_453 = spell(
    id=453,
    name='Mind Soothe',
    school=School.SHADOW,
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
    spell_icon_id=1487,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 2228224, 'AttributesEx2': 524288, 'AttributesEx3': 196608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Reduced distance at which target will attack.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Soothes the target, reducing the range at which it will attack you by $s1 yards.  Only affects Humanoid targets.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_2': 64, 'SpellClassSet': 6, 'SpellLevel': 20, 'SpellVisualID_1': 6440, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetCreatureType': 64},
)


dispel_magic_527 = spell(
    id=527,
    name='Dispel Magic',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=14,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.DISPEL, implicit_target_a=25, misc_value=1),
    ],
    spell_icon_id=74,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 18); RealPointsPerLevel from rank1→level-60 slope (anchor rank 988, rank 2); coefficient/cast_time_ms/mana_cost_pct from max rank (988, rank 2); MaxLevel set to 80. '
          'docs/reworks/priest-new-spells.md ("Spell Changes"): usable on enemies to remove 1 beneficial magic effect, rolled baseline from the old Absolution capstone. implicit_target_a=25 (TARGET_UNIT_TARGET_ANY) already permits enemy targeting at the engine level with no code change needed - confirmed via SpellInfo::CheckExplicitTarget (the friend/foe gate only fires for TARGET_FLAG_UNIT_ENEMY/ALLY masks, which TARGET_UNIT_TARGET_ANY does not set) and Unit::GetDispellableAuraList (Unit.cpp), which already branches purely on GetReactionTo: a friendly target strips harmful DISPEL_MAGIC auras, an unfriendly target strips positive ones. The Description_Lang_enUS text pulled from the client already describes both cases ("harmful...from a friend or...beneficial...from an enemy"), consistent with this already being live Blizzard behavior for this spell. What did need a fix: the dispel charge count came from points_per_level=0.0238 with no base_points, which only coincidentally lands on 1 charge at level 80 rather than being an explicit "remove 1 effect" design. Removed points_per_level entirely; base_points is now left unset, which - per this repo\'s base_points-is-live-value-minus-1 convention (Effect defaults to base_points=0, die_sides=1) - yields a deterministic 1 charge at every level, the same pattern cure_disease_528 already uses for its own single-charge dispel.',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 18, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Dispels magic on the target, removing $s1 harmful $lspell:spells; from a friend or $s1 beneficial $lspell:spells; from an enemy.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 160, 'ShapeshiftMask': 134217728, 'SpellClassMask_2': 1, 'SpellClassSet': 6, 'SpellLevel': 18, 'SpellVisualID_1': 86, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


cure_disease_528 = spell(
    id=528,
    name='Cure Disease',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=12,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.DISPEL, implicit_target_a=21, misc_value=3),
    ],
    spell_icon_id=330,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 14, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Removes $s1 $ldisease:diseases; from the friendly target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 1, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 14, 'SpellVisualID_1': 377, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


abolish_disease_552 = spell(
    id=552,
    name='Abolish Disease',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=329728,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=12,
    range_yards=40.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=21, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=3000, trigger_spell=10872),
        Effect(type=EffectType.DISPEL, implicit_target_a=21, misc_value=3),
    ],
    spell_icon_id=264,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 32768, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Attempts to dispel $10872s1 disease every $t1 seconds.', 'BaseLevel': 32, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Attempts to cure $s2 disease effect on the target, and $10872s1 more disease effect every $t1 seconds for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 1, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 32, 'SpellVisualID_1': 377, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


smite_585 = spell(
    id=585,
    name='Smite',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=2500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=15,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=12, points_per_level=8.7561, die_sides=5, implicit_target_a=6),
    ],
    spell_icon_id=237,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1→top rank's own top level (83, chain has a gap at 60) slope (anchor rank 48123, rank 12); coefficient/cast_time_ms/mana_cost_pct from max rank (48123, rank 12); MaxLevel set to 80",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Smite an enemy for $s1 Holy damage.', 'EffectBonusMultiplier_1': 0.7139999866485596, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'SpellClassMask_1': 128, 'SpellClassSet': 6, 'SpellLevel': 1, 'SpellVisualID_1': 128, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
scripted_by(smite_585, 'spell_pri_surge_of_light_consume')  # Holy (5,0) Surge of Light


fade_586 = spell(
    id=586,
    name='Fade',
    school=School.SHADOW,
    attributes=327680,
    category=82,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=30000,
    mana_cost=0,
    mana_cost_pct=15,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-90000001, implicit_target_a=1, apply_aura=103),
    ],
    spell_icon_id=331,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Reduced threat level.', 'BaseLevel': 8, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Fade out, temporarily reducing all your threat for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 16384, 'SpellClassMask_2': 4096, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 8, 'SpellVisualID_1': 72, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


inner_fire_588 = spell(
    id=588,
    name='Inner Fire',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=14,
    range_yards=0.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=314, points_per_level=22.5, implicit_target_a=1, apply_aura=22, misc_value=1),
    ],
    spell_icon_id=51,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 12); RealPointsPerLevel from rank1→level-60 slope (anchor rank 10952, rank 6); coefficient/cast_time_ms/mana_cost_pct from max rank (48168, rank 9); MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases armor by $s1.', 'BaseLevel': 12, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A burst of Holy energy fills the caster, increasing armor by $s1.  Each melee or ranged damage hit against the priest will remove one charge.  Lasts $d or until $n charges are used.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 20, 'ProcTypeMask': 680, 'RangeIndex': 1, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 2, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 12, 'SpellVisualID_1': 211, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


shadow_word_pain_589 = spell(
    id=589,
    name='Shadow Word: Pain',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=22,
    range_yards=30.0,
    duration_ms=18000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, points_per_level=2.1964, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
    ],
    spell_icon_id=234,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 4); RealPointsPerLevel from rank1→level-60 slope (anchor rank 10894, rank 8); coefficient/cast_time_ms/mana_cost_pct from max rank (48125, rank 12); MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx4': 1048576, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s1 Shadow damage every $t1 seconds.', 'BaseLevel': 4, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A word of darkness that causes $o1 Shadow damage over $d.', 'EffectBasePoints_2': -1, 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 32768, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 4, 'SpellVisualID_1': 71, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
# Priest Shadow rework (SHADOW.md "Scripts on stock spells"): row unchanged - OnEffectPeriodic
# tentacle spawn roll (ignoring the shared ICD) while Surrender to Madness is active.
scripted_by(shadow_word_pain_589, 'spell_pri_shadow_word_pain_surrender')


prayer_of_healing_596 = spell(
    id=596,
    name='Prayer of Healing',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=48,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=300, points_per_level=23.2, die_sides=21, implicit_target_a=21, implicit_target_b=37, radius_yards=30.0),
    ],
    spell_icon_id=540,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 30); RealPointsPerLevel from rank1→level-60 slope (anchor rank 25316, rank 5); coefficient/cast_time_ms/mana_cost_pct from max rank (48072, rank 7); MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 30, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "A powerful prayer heals the friendly target's party members within $a1 yards for $s1.", 'EffectBonusMultiplier_1': 0.5260000228881836, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_1': 512, 'SpellClassSet': 6, 'SpellLevel': 30, 'SpellVisualID_1': 194, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


power_word_shield_600 = spell(
    id=600,
    name='Power Word: Shield',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    mechanic=19,
    attributes=327680,
    category=56,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=4000,
    mana_cost=0,
    mana_cost_pct=23,
    range_yards=40.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=157, points_per_level=1.600000023841858, implicit_target_a=21, apply_aura=69, misc_value=127),
    ],
    spell_icon_id=566,
    notes='superseded rank kept in priest.csv: still referenced by item_template 3122 (Codex of Holy Word: Shield III) spellid_2, not creature-only',
    raw_overrides={'AttributesEx2': 2621440, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Absorbs damage.', 'BaseLevel': 18, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Draws on the soul of the friendly target to shield them, absorbing $s1 damage.  Lasts $d.  While the shield holds, spellcasting will not be interrupted by damage.  Once shielded, the target cannot be shielded again for $6788d.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ExcludeTargetAuraSpell': 6788, 'InterruptFlags': 8, 'MaxLevel': 23, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 1, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 18, 'SpellPriority': 50, 'SpellVisualID_1': 784, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


mind_control_605 = spell(
    id=605,
    name='Mind Control',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    mechanic=Mechanic.CHARM,
    attributes=1075118080,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=12,
    range_yards=20.0,
    duration_ms=60000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=31, points_per_level=1.0, implicit_target_a=6, apply_aura=2, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-26, mechanic=8, implicit_target_a=6, apply_aura=138),
    ],
    spell_icon_id=235,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 67248133, 'AttributesEx2': 524352, 'AttributesEx4': 536872960, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Charmed.  Time between attacks increased by $s3%.', 'BaseLevel': 30, 'CastingTimeIndex': 14, 'ChannelInterruptFlags': 27692, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Controls a humanoid mind up to level $s1, but increases the time between its attacks by $s3%.  Lasts up to $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 131072, 'SpellClassSet': 6, 'SpellLevel': 30, 'SpellVisualID_1': 137, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetCreatureType': 64},
)


shadow_protection_976 = spell(
    id=976,
    name='Shadow Protection',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=31,
    range_yards=30.0,
    duration_ms=600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, points_per_level=1.0, implicit_target_a=21, apply_aura=143, misc_value=32),
    ],
    spell_icon_id=207,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 30); RealPointsPerLevel from rank1→level-60 slope (anchor rank 10958, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (48169, rank 5); MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Shadow resistance increased by $s1.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the target's resistance to Shadow spells by $s1 for $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 256, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 30, 'SpellPriority': 50, 'SpellVisualID_1': 27, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


power_word_fortitude_1243 = spell(
    id=1243,
    name='Power Word: Fortitude',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=27,
    range_yards=30.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, points_per_level=0.8644, implicit_target_a=21, apply_aura=AuraType.MOD_STAT, misc_value=2),
    ],
    spell_icon_id=685,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1→level-60 slope (anchor rank 10938, rank 6); coefficient/cast_time_ms/mana_cost_pct from max rank (48161, rank 8); MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 524288, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases Stamina by $s1.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Power infuses the target, increasing their Stamina by $s1 for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 8, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 1, 'SpellVisualID_1': 278, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


levitate_1706 = spell(
    id=1706,
    name='Levitate',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=30.0,
    duration_ms=120000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=57, apply_aura=105),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=57, apply_aura=106),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=57, apply_aura=104),
    ],
    spell_icon_id=79,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 524288, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Levitating.', 'AuraInterruptFlags': 131074, 'BaseLevel': 34, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Allows the friendly party or raid target to levitate, floating a few feet above the ground.  While levitating, the target will fall at a reduced speed and travel over water.  Any damage will cancel the effect.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17056, 'ShapeshiftExclude': 335544320, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 2147483648, 'SpellClassMask_2': 4096, 'SpellClassMask_3': 1025, 'SpellClassSet': 6, 'SpellLevel': 34, 'SpellVisualID_1': 6768, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


resurrection_2006 = spell(
    id=2006,
    name='Resurrection',
    school=School.HOLY,
    attributes=268500992,
    cast_time_ms=10000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=60,
    range_yards=30.0,
    effects=[
        Effect(type=113, base_points=69, points_per_level=13.6, misc_value=135),
    ],
    spell_icon_id=121,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1→level-60 slope (anchor rank 20770, rank 5); coefficient/cast_time_ms/mana_cost_pct from max rank (48171, rank 7); MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 10, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Brings a dead player back to life with $s1 health and $q1 mana.  Cannot be cast when in combat.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'SpellClassMask_1': 1073741824, 'SpellClassSet': 6, 'SpellLevel': 10, 'SpellPriority': 50, 'SpellVisualID_1': 41, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Targets': 32768},
)


lesser_heal_2050 = spell(
    id=2050,
    name='Lesser Heal',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=2500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=27,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=45, points_per_level=6.9286, die_sides=11, implicit_target_a=21),
    ],
    spell_icon_id=682,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1→top rank's own top level (15, chain has a gap at 60) slope (anchor rank 2053, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (2053, rank 3); MaxLevel set to 80",
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heal your target for $s1.', 'EffectBonusMultiplier_1': 0.8389999866485596, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_1': 262144, 'SpellClassSet': 6, 'SpellLevel': 1, 'SpellPriority': 50, 'SpellVisualID_1': 285, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


lesser_heal_2052 = spell(
    id=2052,
    name='Lesser Heal',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=2000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=21,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=70, points_per_level=1.100000023841858, die_sides=15, implicit_target_a=21),
    ],
    spell_icon_id=682,
    notes='superseded rank kept in priest.csv: still referenced by item_template 5205 (Sprouted Frond) spellid_1, not creature-only',
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 4, 'CastingTimeIndex': 5, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heal your target for $s1.', 'EffectBonusMultiplier_1': 0.4309999942779541, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 9, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_1': 262144, 'SpellClassSet': 6, 'SpellLevel': 4, 'SpellPriority': 50, 'SpellVisualID_1': 285, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


heal_2054 = spell(
    id=2054,
    name='Heal',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=32,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=294, points_per_level=19.087, die_sides=47, implicit_target_a=21),
    ],
    spell_icon_id=104,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 16); RealPointsPerLevel from rank1→top rank's own top level (39, chain has a gap at 60) slope (anchor rank 6064, rank 4); coefficient/cast_time_ms/mana_cost_pct from max rank (6064, rank 4); MaxLevel set to 80",
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 16, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heal your target for $s1.', 'EffectBonusMultiplier_1': 1.6109999418258667, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_1': 1024, 'SpellClassSet': 6, 'SpellLevel': 16, 'SpellPriority': 50, 'SpellVisualID_1': 135, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


greater_heal_2060 = spell(
    id=2060,
    name='Greater Heal',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=32,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=45, points_per_level=37.8101, die_sides=115, implicit_target_a=21),
    ],
    spell_icon_id=241,
    notes="re-anchored for the Priest heal-line collapse (Lesser Heal/Heal retired from trainers, Greater Heal is now the one heal spell learned at level 1): base_points/BaseLevel/SpellLevel moved from rank1's old level-40 anchor down to Lesser Heal rank1's (2050) level-1 value (45); RealPointsPerLevel recomputed as a straight line from that level-1 value to this spell's own previous level-80 ceiling (898 + 40*53.35 = 3032), so max-level healing is unchanged; die_sides/cast_time_ms/mana_cost_pct/coefficient kept as before (from max rank 48063, rank 9). See docs/.master-todo-list.md.",
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A slow casting spell that heals a single target for $s1.', 'EffectBonusMultiplier_1': 1.6109999418258667, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_1': 4096, 'SpellClassSet': 6, 'SpellLevel': 1, 'SpellPriority': 50, 'SpellVisualID_1': 57, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
# Auto-learned at character creation, same as Lesser Heal (2050, SkillLineAbility.dbc ID 2313,
# AcquireMethod=2) was before the heal-line collapse moved that role onto Greater Heal - confirmed
# by reading the stock reconstructed row for this spell (ID 3777, SkillLine 56, ClassMask 16,
# MinSkillLineRank 1) via lib/state.py's load_existing_rows(), which is byte-identical to 2050's
# row except AcquireMethod was left at 0 (trainer-taught) instead of flipped to 2 (client
# auto-learns it once skill line 56 rank >= MinSkillLineRank, i.e. immediately at character
# creation) when this spell was re-anchored to level 1. All other columns kept at their stock
# values (raw_overrides only touches AcquireMethod) - explicit field values below match row 3777
# exactly so the regenerated row is identical to stock apart from that one flag.
skill_line_ability(id=3777, skill_line=56, spell_id=greater_heal_2060.id, class_mask=16,
                    min_skill_line_rank=1, raw_overrides={'AcquireMethod': 2})
# Retired from the Priest trainers now that it's auto-known - same treatment Heal (2054) got in
# data/sql/updates/db_world/2026_09_06_01.sql when Greater Heal absorbed its old level range. That
# DELETE is hand-written in data/sql/updates/pending_db_world/rev_1789876824693627136.sql, not
# emitted here: the TrainerId 11/208 rows for SpellId 2060 come from mod-progression's own
# phase_00-trainer_spell.sql, and trained_by()'s registry only emits rows it's explicitly told
# about, so removing a module-sourced row needs a hand-written DELETE, not a trained_by() call.


flash_heal_2061 = spell(
    id=2061,
    name='Flash Heal',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=18,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=192, points_per_level=15.875, die_sides=45, implicit_target_a=21),
    ],
    spell_icon_id=242,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1→level-60 slope (anchor rank 10917, rank 7); coefficient/cast_time_ms/mana_cost_pct from max rank (48071, rank 11); MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals a friendly target for $s1.', 'EffectBonusMultiplier_1': 0.8069999814033508, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_1': 2048, 'SpellClassSet': 6, 'SpellLevel': 20, 'SpellPriority': 50, 'SpellVisualID_1': 3077, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
scripted_by(flash_heal_2061, 'spell_pri_surge_of_light_consume')  # Holy (5,0) Surge of Light


mind_vision_2096 = spell(
    id=2096,
    name='Mind Vision',
    school=School.SHADOW,
    attributes=67174400,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=100.0,
    duration_ms=60000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=25, apply_aura=1, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=25, apply_aura=68),
    ],
    spell_icon_id=502,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 22); RealPointsPerLevel from rank1→level-60 slope (anchor rank 10909, rank 2); coefficient/cast_time_ms/mana_cost_pct from max rank (10909, rank 2); MaxLevel set to 80',
    raw_overrides={'AttributesEx': 67773444, 'AttributesEx2': 524300, 'AttributesEx3': 196608, 'AttributesEx4': 65536, 'AttributesEx5': 2097152, 'AttributesEx6': 12, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': "Sight granted through target's eyes.", 'BaseLevel': 22, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31772, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Allows the caster to see through the target's eyes for $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 9, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 67108864, 'SpellClassMask_2': 2147483648, 'SpellClassSet': 6, 'SpellLevel': 22, 'SpellVisualID_1': 4839, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


devouring_plague_2944 = spell(
    id=2944,
    name='Devouring Plague',
    school=School.SHADOW,
    dispel=DispelType.DISEASE,
    mechanic=22,
    attributes=65536,
    category=691,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=25,
    range_yards=30.0,
    duration_ms=24000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=18, points_per_level=2.35, implicit_target_a=6, apply_aura=AuraType.PERIODIC_LEECH, amplitude=3000),
    ],
    spell_icon_id=3789,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1→level-60 slope (anchor rank 19280, rank 6); coefficient/cast_time_ms/mana_cost_pct from max rank (48300, rank 9); MaxLevel set to 80. '
          'docs/reworks/priest-new-spells.md ("Spell Changes"): learn level moved from 20 to 14.',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx5': 32, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Causes $s1 damage every $t1 seconds, healing the caster.', 'BaseLevel': 14, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Afflicts the target with a disease that causes $o1 Shadow damage over $d. 15% of damage caused by the Devouring Plague heals the caster. This spell can only affect one target at a time.', 'EffectBonusMultiplier_1': 0.1850000023841858, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 0.15000000596046448, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 33554432, 'SpellClassMask_2': 4096, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 14, 'SpellPriority': 50, 'SpellVisualID_1': 346, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
# TrainerId 208 is the live Priest trainer (confirmed via lib/trainer_state.py's
# load_trainer_index().trainer_problems() - TrainerId 11, which this spell's pulled trainer_spell
# data otherwise sits under, has zero creature_default_trainer rows and is dead). This spell
# already had a 208 row (ReqLevel 20/MoneyCost 3000, pre-dating this rework) - trained_by()'s own
# "skip what's already live, DELETE+INSERT the rest" emission updates it in place to match the new
# level 14 rather than leaving it stale. MoneyCost 1200 matches this trainer's own real level-14
# rows (528/8122, both 1200c) rather than keeping the old level-20 price on the new lower level.
trained_by(devouring_plague_2944, trainer_id=208, req_level=14, money_cost=1200)
# Priest Shadow rework (SHADOW.md "Core hardcode migration owed by this pass" / PLAN §6.8):
# Improved Devouring Plague's instant chunk (SpellAuras.cpp:1499, hardcoded OnEffectApply cast of
# 63675) moves to a spell_pri_devouring_plague AuraScript bound directly to this stock spell.
scripted_by(devouring_plague_2944, 'spell_pri_devouring_plague')


heal_6063 = spell(
    id=6063,
    name='Heal',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=32,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=565, points_per_level=4.0, die_sides=77, implicit_target_a=21),
    ],
    spell_icon_id=684,
    notes='superseded rank kept in priest.csv: still referenced by item_template 8993 (Codex of Shadow Protection II) spellid_2, not creature-only',
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 28, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heal your target for $s1.', 'EffectBonusMultiplier_1': 1.6109999418258667, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 33, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_1': 1024, 'SpellClassSet': 6, 'SpellLevel': 28, 'SpellPriority': 50, 'SpellVisualID_1': 135, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


fear_ward_6346 = spell(
    id=6346,
    name='Fear Ward',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=30.0,
    duration_ms=180000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=21, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=5),
    ],
    spell_icon_id=158,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AttributesEx4': 524288, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Warded against Fear.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Wards the friendly target against Fear.  The next Fear effect used against the target will fail, using up the ward.  Lasts $d.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 139264, 'SpellClassMask_1': 2147483648, 'SpellClassMask_2': 33558528, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 20, 'SpellVisualID_1': 343, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


mind_blast_8092 = spell(
    id=8092,
    name='Mind Blast',
    school=School.SHADOW,
    attributes=65536,
    category=19,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=8000,
    mana_cost=0,
    mana_cost_pct=17,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=38, points_per_level=9.38, die_sides=5, implicit_target_a=6),
    ],
    spell_icon_id=95,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1→level-60 slope (anchor rank 10947, rank 9); coefficient/cast_time_ms/mana_cost_pct from max rank (48127, rank 13); MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 10, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Blasts the target for $s1 Shadow damage.', 'EffectBonusMultiplier_1': 0.42899999022483826, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 8192, 'SpellClassSet': 6, 'SpellLevel': 10, 'SpellVisualID_1': 3057, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
# Priest Shadow rework (SHADOW.md "Scripts on stock spells"): row unchanged, one script class
# handles all three Mind Blast hooks (Tentacles of Madness 3,0 spawn roll, Darkness 0,2's free-cast
# consumption, Void-touched Mind 7,2's Voidform extension, Madness generation).
scripted_by(mind_blast_8092, 'spell_pri_mind_blast_shadow')


psychic_scream_8122 = spell(
    id=8122,
    name='Psychic Scream',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    mechanic=Mechanic.FEAR,
    attributes=327680,
    category=43,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=30000,
    mana_cost=0,
    mana_cost_pct=15,
    range_yards=0.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=22, implicit_target_b=15, apply_aura=AuraType.MOD_FEAR, radius_yards=8.0),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=22, implicit_target_b=15, apply_aura=AuraType.MOD_INCREASE_SPEED, radius_yards=8.0),
    ],
    spell_icon_id=1488,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 14); RealPointsPerLevel from rank1→level-60 slope (anchor rank 10890, rank 4); coefficient/cast_time_ms/mana_cost_pct from max rank (10890, rank 4); MaxLevel set to 80',
    raw_overrides={'AttributesEx': 136, 'AttributesEx2': 524288, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Running in Fear.', 'AuraInterruptFlags': 4718592, 'BaseLevel': 14, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The caster lets out a psychic scream, causing $i enemies within $a1 yards to flee for $d.  Damage caused may interrupt the effect.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'MaxTargets': 2, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 664232, 'RangeIndex': 1, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 65536, 'SpellClassSet': 6, 'SpellLevel': 14, 'SpellPriority': 50, 'SpellVisualID_1': 247, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


mana_burn_8129 = spell(
    id=8129,
    name='Mana Burn',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=14,
    range_yards=30.0,
    effects=[
        Effect(type=62, base_points=9, implicit_target_a=6),
    ],
    spell_icon_id=212,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 24, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Destroy $m1% of the target's mana (up to a maximum of ${$m1*2}% of your own maximum mana). For each mana destroyed in this way, the target takes 0.5 Shadow damage.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 0.5, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 29, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 16, 'SpellClassSet': 6, 'SpellLevel': 24, 'SpellVisualID_1': 3076, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


shackle_undead_9484 = spell(
    id=9484,
    name='Shackle Undead',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    mechanic=20,
    attributes=1074855936,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=9,
    range_yards=30.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
    ],
    spell_icon_id=27,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1→level-60 slope (anchor rank 10955, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (10955, rank 3); MaxLevel set to 80',
    raw_overrides={'AttributesEx': 262144, 'AttributesEx2': 524288, 'AttributesEx5': 32, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Shackled.', 'AuraInterruptFlags': 2, 'BaseLevel': 20, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shackles the target undead enemy for up to $d.  The shackled unit is unable to move, attack or cast spells.  Any damage caused will release the target.  Only one target can be shackled at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 1073741824, 'SpellClassMask_2': 67112960, 'SpellClassSet': 6, 'SpellLevel': 20, 'SpellVisualID_1': 1507, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetCreatureType': 32},
)


power_word_fortitude_10937 = spell(
    id=10937,
    name='Power Word: Fortitude',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=27,
    range_yards=30.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=42, implicit_target_a=21, apply_aura=AuraType.MOD_STAT, misc_value=2),
    ],
    spell_icon_id=685,
    notes='superseded rank kept in priest.csv: still referenced by quest_template 5217/5220/5223 RewardSpell, not creature-only',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 524288, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases Stamina by $s1.', 'BaseLevel': 48, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Power infuses the target, increasing their Stamina by $s1 for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 58, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 8, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 48, 'SpellVisualID_1': 278, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


power_word_fortitude_10938 = spell(
    id=10938,
    name='Power Word: Fortitude',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=27,
    range_yards=30.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=53, implicit_target_a=21, apply_aura=AuraType.MOD_STAT, misc_value=2),
    ],
    spell_icon_id=685,
    notes='superseded rank kept in priest.csv: still referenced by quest_template 5226 RewardSpell, not creature-only',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 524288, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases Stamina by $s1.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Power infuses the target, increasing their Stamina by $s1 for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 70, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 6', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 8, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 60, 'SpellVisualID_1': 278, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


divine_spirit_14752 = spell(
    id=14752,
    name='Divine Spirit',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=26,
    range_yards=30.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=16, points_per_level=0.7667, implicit_target_a=21, apply_aura=AuraType.MOD_STAT, misc_value=4),
    ],
    spell_icon_id=1879,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 30); RealPointsPerLevel from rank1→level-60 slope (anchor rank 27841, rank 4); coefficient/cast_time_ms/mana_cost_pct from max rank (48073, rank 6); MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases Spirit by $s1.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Holy power infuses the target, increasing their Spirit by $s1 for $d.', 'EffectBasePoints_2': -1, 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 32, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 30, 'SpellVisualID_1': 193, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


holy_fire_14914 = spell(
    id=14914,
    name='Holy Fire',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    category=451,
    cast_time_ms=2000,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    mana_cost=0,
    mana_cost_pct=11,
    range_yards=30.0,
    duration_ms=7000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=101, points_per_level=13.425, die_sides=27, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=2, points_per_level=0.375, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=1000),
    ],
    spell_icon_id=156,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1→level-60 slope (anchor rank 15261, rank 8); coefficient/cast_time_ms/mana_cost_pct from max rank (48135, rank 11); MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s2 Holy damage every $t2 seconds.', 'BaseLevel': 20, 'CastingTimeIndex': 5, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Consumes the enemy in Holy flames that cause $s1 Holy damage and an additional $o2 Holy damage over $d.', 'EffectBonusMultiplier_1': 0.5709999799728394, 'EffectBonusMultiplier_2': 0.024000000208616257, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'SpellClassMask_1': 1048576, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 20, 'SpellPriority': 50, 'SpellVisualID_1': 3400, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


holy_nova_15237 = spell(
    id=15237,
    name='Holy Nova',
    school=School.HOLY,
    attributes=65536,
    category=431,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=20,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=27, points_per_level=3.825, die_sides=5, implicit_target_a=22, implicit_target_b=15, radius_yards=10.0),
    ],
    spell_icon_id=1874,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1→level-60 slope (anchor rank 27801, rank 6); coefficient/cast_time_ms/mana_cost_pct from max rank (48078, rank 9); MaxLevel set to 80',
    raw_overrides={'AttributesEx': 136, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes an explosion of holy light around the caster, causing $15237s1 Holy damage to all enemy targets within $15237a1 yards and healing all party members within $23455a1 yards for $23455s1.  These effects cause no threat.', 'EffectBonusMultiplier_1': 0.16099999845027924, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassMask_1': 4194304, 'SpellClassSet': 6, 'SpellLevel': 20, 'SpellVisualID_1': 3643, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


prayer_of_fortitude_21562 = spell(
    id=21562,
    name='Prayer of Fortitude',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=69,
    range_yards=40.0,
    duration_ms=3600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=42, points_per_level=0.9167, implicit_target_a=56, apply_aura=AuraType.MOD_STAT, misc_value=2, radius_yards=100.0),
    ],
    spell_icon_id=1669,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 48); RealPointsPerLevel from rank1→level-60 slope (anchor rank 21564, rank 2); coefficient/cast_time_ms/mana_cost_pct from max rank (48162, rank 4); MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 524288, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases Stamina by $s1.', 'BaseLevel': 48, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Power infuses all party and raid members, increasing their Stamina by $s1 for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17028, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 8, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 48, 'SpellVisualID_1': 278, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


prayer_of_fortitude_21564 = spell(
    id=21564,
    name='Prayer of Fortitude',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=69,
    range_yards=40.0,
    duration_ms=3600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=53, implicit_target_a=56, apply_aura=AuraType.MOD_STAT, misc_value=2, radius_yards=100.0),
    ],
    spell_icon_id=1669,
    notes='superseded rank kept in priest.csv: still referenced by item_template 17414 (Codex: Prayer of Fortitude II) spellid_2, not creature-only',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 524288, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases Stamina by $s1.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Power infuses all party and raid members, increasing their Stamina by $s1 for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 70, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17029, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 8, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 60, 'SpellVisualID_1': 278, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


greater_heal_25314 = spell(
    id=25314,
    name='Greater Heal',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=32,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=1965, points_per_level=8.100000381469727, die_sides=229, implicit_target_a=21),
    ],
    spell_icon_id=241,
    notes='superseded rank kept in priest.csv: still referenced by item_template 21284 (Codex of Greater Heal V) spellid_2, not creature-only',
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A slow casting spell that heals a single target for $s1.', 'EffectBonusMultiplier_1': 1.6109999418258667, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 65, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_1': 4096, 'SpellClassSet': 6, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 57, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


renew_25315 = spell(
    id=25315,
    name='Renew',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=17,
    range_yards=40.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=193, implicit_target_a=21, apply_aura=AuraType.PERIODIC_HEAL, amplitude=3000),
    ],
    spell_icon_id=321,
    notes='superseded rank kept in priest.csv: still referenced by item_template 21285 (Codex of Renew X) spellid_2, not creature-only',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx3': 128, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Healing $s1 damage every $t1 seconds.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals the target for $<total> over $d.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 0.37599998712539673, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 65, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 10', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_1': 64, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellDescriptionVariableID': 30, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 280, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


prayer_of_healing_25316 = spell(
    id=25316,
    name='Prayer of Healing',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=48,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=996, points_per_level=2.5, die_sides=57, implicit_target_a=21, implicit_target_b=37, radius_yards=30.0),
    ],
    spell_icon_id=540,
    notes='superseded rank kept in priest.csv: still referenced by item_template 21287 (Codex of Prayer of Healing V) spellid_2, not creature-only',
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "A powerful prayer heals the friendly target's party members within $a1 yards for $s1.", 'EffectBonusMultiplier_1': 0.5260000228881836, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 69, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_1': 512, 'SpellClassSet': 6, 'SpellLevel': 60, 'SpellVisualID_1': 194, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


prayer_of_fortitude_25392 = spell(
    id=25392,
    name='Prayer of Fortitude',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=69,
    range_yards=40.0,
    duration_ms=3600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=78, implicit_target_a=56, apply_aura=AuraType.MOD_STAT, misc_value=2, radius_yards=100.0),
    ],
    spell_icon_id=1669,
    notes='superseded rank kept in priest.csv: still referenced by item_template 29549 (Codex: Prayer of Fortitude III) spellid_2, not creature-only',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 524288, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases Stamina by $s1.', 'BaseLevel': 70, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Power infuses all party and raid members, increasing their Stamina by $s1 for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17029, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 8, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 70, 'SpellVisualID_1': 278, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


prayer_of_spirit_27681 = spell(
    id=27681,
    name='Prayer of Spirit',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=69,
    range_yards=40.0,
    duration_ms=3600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=39, points_per_level=1.3333, implicit_target_a=56, apply_aura=AuraType.MOD_STAT, misc_value=4, radius_yards=100.0),
    ],
    spell_icon_id=1870,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 60); RealPointsPerLevel from rank1→top rank's own top level (90, chain has a gap at 60) slope (anchor rank 48074, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (48074, rank 3); MaxLevel set to 80",
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 524288, 'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases Spirit by $s1.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Power infuses the target's party and raid members, increasing their Spirit by $s1 for $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 32, 'SpellClassSet': 6, 'SpellLevel': 60, 'SpellVisualID_1': 193, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


prayer_of_shadow_protection_27683 = spell(
    id=27683,
    name='Prayer of Shadow Protection',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=62,
    range_yards=40.0,
    duration_ms=1200000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=59, implicit_target_a=56, apply_aura=143, misc_value=32, radius_yards=100.0),
    ],
    spell_icon_id=1869,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 56); RealPointsPerLevel from rank1→level-60 slope (anchor rank 27683, rank 1); coefficient/cast_time_ms/mana_cost_pct from max rank (48170, rank 3); MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 524288, 'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases Shadow Resistance by $s1.', 'BaseLevel': 56, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Power infuses the target's party and raid members, increasing their Shadow resistance by $s1 for $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17029, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 256, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 56, 'SpellVisualID_1': 27, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


mass_dispel_32375 = spell(
    id=32375,
    name='Mass Dispel',
    school=School.HOLY,
    attributes=536936448,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=33,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.DISPEL, implicit_target_a=31, misc_value=1, radius_yards=15.0),
        Effect(type=EffectType.TRIGGER_SPELL, implicit_target_a=16, trigger_spell=32592, radius_yards=10.0),
        Effect(type=EffectType.TRIGGER_SPELL, base_points=72733, implicit_target_a=1, trigger_spell=72734),
    ],
    spell_icon_id=2267,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 70, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Dispels magic in a $32375a1 yard radius, removing $32375s1 harmful $lspell:spells; from each friendly target and $32375s1 beneficial $lspell:spells; from each enemy target.  Affects a maximum of $32375i friendly targets and $32375i enemy targets.  This dispel is potent enough to remove Magic effects that are normally undispellable.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxTargets': 10, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_2': 128, 'SpellClassSet': 6, 'SpellLevel': 70, 'SpellVisualID_1': 8140, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Targets': 64},
)


shadow_word_death_32379 = spell(
    id=32379,
    name='Shadow Word: Death',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    attributes=327680,
    category=1169,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=12000,
    mana_cost=0,
    mana_cost_pct=12,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=449, points_per_level=13.6364, die_sides=73, implicit_target_a=6),
    ],
    spell_icon_id=1980,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 62); RealPointsPerLevel from rank1→top rank's own top level (84, chain has a gap at 60) slope (anchor rank 48158, rank 4); coefficient/cast_time_ms/mana_cost_pct from max rank (48158, rank 4); MaxLevel set to 80. "
          "docs/reworks/priest-new-spells.md (\"Spell Changes\"): learn level moved from 62 to 30.",
    raw_overrides={'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A word of dark binding that inflicts $s1 Shadow damage to the target.  If the target is not killed by Shadow Word: Death, the caster takes damage equal to the damage inflicted upon the target.', 'EffectBonusMultiplier_1': 0.42899999022483826, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_2': 2, 'SpellClassSet': 6, 'SpellLevel': 30, 'SpellVisualID_1': 8069, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
# This spell's only pulled trainer_spell row was under dead TrainerId 11 (see devouring_plague_2944's
# own trained_by() comment above) - it was never actually trainable in this project until now.
# MoneyCost 10000 matches this trainer's own real level-30 rows (596/976/605, all 10000c).
trained_by(shadow_word_death_32379, trainer_id=208, req_level=30, money_cost=10000)
# Priest Shadow rework (SHADOW.md "Scripts on stock spells"): row unchanged - Deathspeaker (4,1)'s
# backlash-tentacle roll (subject to the shared ICD) and OnKill's kill-tentacle roll (Priest::OnKill,
# no ICD) both live in spell_pri_shadow_word_death, which is already bound.
#
# NO scripted_by() here on purpose. data/sql/base/db_world/spell_script_names.sql already carries
# (-32379, 'spell_pri_shadow_word_death') - the negative-ID "this spell and every rank in its
# spell_ranks chain" form, and 32379 has a real 4-rank chain (32379/32996/48157/48158).
# ObjectMgr::LoadSpellScriptNames expands that into _spellScriptsStore, which is a MULTIMAP: adding
# a positive (32379, ...) row on top does not replace the base row, it registers the script a second
# time for rank 1. Every hook then runs twice - doubled SW:D backlash damage and a doubled
# Deathspeaker roll on every cast. scripted_by()'s own docstring covers the convention; 32379 is the
# only stock spell this rework binds that already has a base row (verified against all ten).


binding_heal_32546 = spell(
    id=32546,
    name='Binding Heal',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=27,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=1041, points_per_level=51.3333, die_sides=297, implicit_target_a=21),
        Effect(type=EffectType.HEAL, base_points=1041, points_per_level=51.3333, die_sides=297, implicit_target_a=1),
    ],
    spell_icon_id=2266,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 64); RealPointsPerLevel from rank1→top rank's own top level (82, chain has a gap at 60) slope (anchor rank 48120, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (48120, rank 3); MaxLevel set to 80. "
          'Priest Holy rework (HOLY.md "Baseline spell edits"): BaseLevel/SpellLevel 64->46 - see the trained_by() call below, the first ever added for this spell (it was live only via the trainer\'s stock data before).',
    raw_overrides={'AttributesEx': 524288, 'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 46, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals a friendly target and the caster for $s1.  Low threat.', 'EffectBonusMultiplier_1': 0.8069999814033508, 'EffectBonusMultiplier_2': 0.8069999814033508, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_2': 4, 'SpellClassSet': 6, 'SpellLevel': 46, 'SpellPriority': 50, 'SpellVisualID_1': 3077, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
# No trained_by() call existed for this spell before (live only via the trainer 208's own stock
# data - HOLY.md "Baseline spell edits"). MoneyCost 18000 extrapolated the same way as
# leap_of_faith_200137's own level-46 row on this trainer (18000c) - same level, same basis.
trained_by(binding_heal_32546, trainer_id=208, req_level=46, money_cost=18000)


prayer_of_mending_33076 = spell(
    id=33076,
    name='Prayer of Mending',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    category=1181,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=10000,
    mana_cost=0,
    mana_cost_pct=15,
    range_yards=40.0,
    effects=[
        Effect(type=142, base_points=799, points_per_level=15.1875, implicit_target_a=57, trigger_spell=prayer_of_mending_41635.id),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=57, trigger_spell=41637),
    ],
    spell_icon_id=2219,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 68); RealPointsPerLevel from rank1→top rank's own top level (84, chain has a gap at 60) slope (anchor rank 48113, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (48113, rank 3); MaxLevel set to 80. "
          "docs/reworks/priest-new-spells.md (\"Spell Changes\"): learn level moved from 68 to 28.",
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx3': 67108864, 'AttributesEx7': 1073741824, 'AuraDescription_Lang_Mask': 16712190, 'BaseLevel': 28, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Places a spell on the target that heals them for $s1 the next time they take damage.  When the heal occurs, Prayer of Mending jumps to a party or raid member within $41635a1 yards.  Jumps up to $n times and lasts $41635d after each jump.  This spell can only be placed on one target at a time.', 'EffectBonusMultiplier_1': 0.8069999814033508, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 5, 'ProcTypeMask': 699048, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_2': 32, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 28, 'SpellVisualID_1': 8070, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
# This spell's only pulled trainer_spell row was under dead TrainerId 11 (see devouring_plague_2944's
# own trained_by() comment above) - it was never actually trainable in this project until now.
# MoneyCost 8000 interpolated between this trainer's real level-24 (5000c) and level-30 (10000c) rows
# - no exact level-28 precedent exists on this trainer.
trained_by(prayer_of_mending_33076, trainer_id=208, req_level=28, money_cost=8000)


shadowfiend_34433 = spell(
    id=34433,
    name='Shadowfiend',
    school=School.SHADOW,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=300000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.SUMMON, die_sides=0, implicit_target_a=53, misc_value=19668),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=1, trigger_spell=41967),
    ],
    spell_icon_id=2296,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268435457, 'AttributesEx2': 524288, 'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 66, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Creates a shadowy fiend to attack the target.  Caster receives $34650s1% mana when the Shadowfiend attacks. Damage taken by area of effect attacks is reduced. Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 1561, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 1073741824, 'SpellClassMask_2': 256, 'SpellClassSet': 6, 'SpellLevel': 66, 'SpellVisualID_1': 8208, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


prayer_of_shadow_protection_39374 = spell(
    id=39374,
    name='Prayer of Shadow Protection',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=62,
    range_yards=40.0,
    duration_ms=1200000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=69, implicit_target_a=56, apply_aura=143, misc_value=32, radius_yards=100.0),
    ],
    spell_icon_id=1869,
    notes='superseded rank kept in priest.csv: still referenced by item_template 31837 (Codex: Prayer of Shadow Protection II) spellid_2, not creature-only',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 524288, 'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases Shadow Resistance by $s1.', 'BaseLevel': 70, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Power infuses the target's party and raid members, increasing their Shadow resistance by $s1 for $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17029, 'ShapeshiftMask': 134217728, 'SpellClassMask_1': 256, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 70, 'SpellVisualID_1': 27, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


mind_sear_48045 = spell(
    id=48045,
    name='Mind Sear',
    school=School.SHADOW,
    attributes=4259840,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=28,
    range_yards=30.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=6, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=1000, trigger_spell=mind_sear_49821.id),
    ],
    spell_icon_id=2895,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 75); RealPointsPerLevel from rank1→top rank's own top level (84, chain has a gap at 60) slope (anchor rank 53023, rank 2); coefficient/cast_time_ms/mana_cost_pct from max rank (53023, rank 2); MaxLevel set to 80. "
          "docs/reworks/priest-new-spells.md (\"Spell Changes\"): learn level moved from 75 to 44. The periodic-tick spell (mind_sear_49821, priest_trigger_spells.py) is trigger-only and never player-cast, so it has no independent level gate to change.",
    raw_overrides={'AttributesEx': 132, 'AttributesEx2': 524288, 'AttributesEx5': 8192, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Causing shadow damage to all targets within $49821a1 yards.', 'BaseLevel': 44, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31788, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes an explosion of shadow magic around the enemy target, causing $49821s1 Shadow damage every $T1 sec for $d to all enemies within $49821a1 yards around the target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_2': 1048576, 'SpellClassSet': 6, 'SpellLevel': 44, 'SpellVisualID_1': 12121, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
# This spell's only pulled trainer_spell row was under dead TrainerId 11 (see devouring_plague_2944's
# own trained_by() comment above) - it was never actually trainable in this project until now.
# MoneyCost 17000 extrapolated from this trainer's real level-30/32/34 rows (10000/11000/12000,
# ~500c/level) - no data exists past level 34 on this trainer to anchor to more precisely; flagged
# as a first-pass estimate like this rework's other placeholder tuning numbers.
trained_by(mind_sear_48045, trainer_id=208, req_level=44, money_cost=17000)


divine_hymn_64843 = spell(
    id=64843,
    name='Divine Hymn',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=9,
    range_yards=40.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=1000, trigger_spell=divine_hymn_64844.id),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3209,
    notes='pulled from existing data. '
          'docs/reworks/priest-new-spells.md: "Heals all party or raid members within 40 yards for 1000 + 1.0 coefficient over 5 sec. Each heal increases all targets\' healing taken by 4% for 15 sec, stacking." Cooldown 480000->180000 (3 min, per the design doc header - not the 8 min a different draft doc implied, confirmed with the user), mana_cost_pct 63->9, duration_ms 8000->5000 and amplitude 2000->1000 (5 ticks over 5 sec instead of 4 over 8, so trigger_spell=divine_hymn_64844 fires once per second for the full channel), BaseLevel/SpellLevel 80->60 (raw_overrides below). The actual heal amount, target selection (everyone in range now, not just the 3 lowest-health) and the stacking healing-taken buff all live on divine_hymn_64844 (priest_trigger_spells.py, migrated out of npc.csv in the same change) - this row is just the channel/trigger shell. Effect index 1 (a small self DUMMY aura, base_points=2/live 3) is unchanged pulled data, left as-is - its purpose wasn\'t touched by this rework and no reference to it appears in the design doc.',
    raw_overrides={'AttributesEx': 536870980, 'AttributesEx2': 1074266116, 'AttributesEx3': 1073741824, 'AttributesEx4': 64, 'AttributesEx5': 8192, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Reciting Divine Hymn, healing nearby friendly party or raid targets for $64844s1 every $t1 sec for $d.', 'AuraInterruptFlags': 131072, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31788, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals all party or raid members within $64844a1 yards for $64844s1 every $64843t1 sec for $64843d. Each heal increases the target\'s healing taken by $64844s2% for $64844d, stacking.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 13, 'MaxLevel': 84, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_2': 4194304, 'SpellClassSet': 6, 'SpellLevel': 60, 'SpellVisualID_1': 10671, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
# This spell's only pulled trainer_spell row was under dead TrainerId 11 (see devouring_plague_2944's
# own trained_by() comment above) - it was never actually trainable in this project until now.
# MoneyCost 25000 extrapolated from this trainer's real level-30/32/34 rows (~500c/level past 30) -
# first-pass estimate, no data exists this high on this specific trainer to anchor to more precisely.
trained_by(divine_hymn_64843, trainer_id=208, req_level=60, money_cost=25000)


hymn_of_hope_64901 = spell(
    id=64901,
    name='Hymn of Hope',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=360000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=40.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=2000, trigger_spell=64904),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2218,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 536870980, 'AttributesEx2': 524288, 'AttributesEx4': 64, 'AttributesEx5': 8192, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Reciting Hymn of Hope, restoring $64904s1% mana to nearby friendly party or raid targets most in need every $t1 sec for $d.', 'AuraInterruptFlags': 131072, 'BaseLevel': 80, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31788, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Restores $64904s1% mana to $64901s2 nearby low mana friendly party or raid targets every $64901t1 sec for $64901d, and increases their total maximum mana by $64904s2% for $64904d. Maximum of $*4;s2 mana restores. The Priest must channel to maintain the spell.', 'EffectBonusMultiplier_1': 0.12700000405311584, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 13, 'MaxLevel': 84, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'SpellClassMask_3': 16, 'SpellClassSet': 6, 'SpellLevel': 80, 'SpellVisualID_1': 12858, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


lightwell_724 = spell(
    id=724,
    name='Lightwell',
    school=School.HOLY,
    attributes=65536,
    category=1145,
    cast_time_ms=500,
    cooldown_ms=0,
    category_cooldown_ms=90000,
    mana_cost=0,
    mana_cost_pct=17,
    range_yards=40.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.SUMMON, implicit_target_a=87, misc_value=31897),
    ],
    spell_icon_id=1878,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 40); RealPointsPerLevel from rank1→level-60 slope (anchor rank 27871, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (48087, rank 6); MaxLevel set to 80. '
          'Priest Holy rework (HOLY.md "Baseline spell edits" / design doc §3): 90 s cooldown added on category_cooldown_ms (this row already used category_cooldown_ms, not cooldown_ms, for its stock 3-min recharge - the field that was actually load-bearing before, so this keeps the same field rather than adding a redundant cooldown_ms). Summon duration 180000->30000: checked src/server/game/Spells/SpellEffects.cpp\'s Spell::EffectSummonType (SUMMON_TYPE_LIGHTWELL branch) - it calls `SummonCreature(entry, *destTarget, properties, duration, ...)` with `duration = m_spellInfo->GetDuration()`, i.e. THIS spell\'s own duration_ms is what controls the summoned Lightwell object\'s lifetime, not any field on the creature_template - so that\'s the one changed. No more clicking: the object auto-heals via npc_pet_pri_lightwell (WP-B, pet_priest.cpp) instead of Lightwell Charges (59907)/Lightwell Renew (7001), which go unused after this pass.',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 40, 'CastingTimeIndex': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Creates a Holy Lightwell that lasts $d. Once per sec, it heals the party or raid member within 20 yds most in need for $200202s1, for up to 10 heals.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 1141, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_1': 1073741824, 'SpellClassSet': 6, 'SpellDescriptionVariableID': 162, 'SpellLevel': 40, 'SpellVisualID_1': 7550, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Targets': 64},
)


mind_flay_15407 = spell(
    id=15407,
    name='Mind Flay',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=9,
    range_yards=30.0,
    duration_ms=3000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-51, mechanic=Mechanic.SNARE, implicit_target_a=6, apply_aura=AuraType.MOD_DECREASE_SPEED),
        Effect(type=EffectType.APPLY_AURA, base_points=14, points_per_level=2.65, implicit_target_a=1, apply_aura=227, amplitude=1000, trigger_spell=58381),
    ],
    spell_icon_id=548,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1→level-60 slope (anchor rank 18807, rank 6); coefficient/cast_time_ms/mana_cost_pct from max rank (48156, rank 9); MaxLevel set to 80',
    raw_overrides={'AttributesEx': 67125252, 'AttributesEx2': 524288, 'AttributesEx5': 134225920, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement speed slowed.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31756, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Assault the target's mind with Shadow energy, causing ${$m3*3} Shadow damage over $d and slowing their movement speed by $s2%.", 'EffectBonusMultiplier_3': 0.2709999978542328, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_3': 1088, 'SpellClassSet': 6, 'SpellLevel': 20, 'SpellVisualID_1': 12637, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
# Priest Shadow rework (SHADOW.md "Scripts on stock spells"): row unchanged - OnEffectPeriodic
# generates 1 Madness/tick (3 during Surrender) and, while Surrender to Madness is active, rolls a
# tentacle spawn on every tick ignoring the shared ICD.
scripted_by(mind_flay_15407, 'spell_pri_mind_flay_madness')


desperate_prayer_19236 = spell(
    id=19236,
    name='Desperate Prayer',
    school=School.HOLY,
    attributes=65536,
    category=671,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=120000,
    mana_cost=0,
    mana_cost_pct=21,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.HEAL, base_points=262, points_per_level=26.525, die_sides=63, implicit_target_a=1),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
    ],
    spell_icon_id=73,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1→level-60 slope (anchor rank 19243, rank 6); coefficient/cast_time_ms/mana_cost_pct from max rank (48173, rank 9); MaxLevel set to 80. '
          'Priest Holy rework (HOLY.md "Baseline spell edits" / design doc row 2,0): new EFFECT_1 (previously unused) MOD_DAMAGE_PERCENT_TAKEN (aura 87) misc_value=127 (physical+all-magic school mask - confirmed against several other classes\' own -X%-damage-taken cooldowns in this codebase using the identical misc_value=127, e.g. deathknight_spells.py/paladin_spells.py/druid_spells.py, rather than assuming), base_points=-21 (stored -1 convention -> live -20%), duration_ms=10000 added at the spell level for this new aura effect to run on (the HEAL effect is instant and does not consume it).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly heals the caster for $s1 and reduces damage taken by 20% for $19236d.  Below 50% health, this heal is always a critical strike.', 'EffectBonusMultiplier_1': 0.8069999814033508, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftExclude': 134217728, 'SpellClassMask_1': 16777216, 'SpellClassSet': 6, 'SpellLevel': 20, 'SpellVisualID_1': 4819, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


circle_of_healing_34861 = spell(
    id=34861,
    name='Circle of Healing',
    school=School.HOLY,
    attributes=65536,
    category=1204,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=6000,
    mana_cost=0,
    mana_cost_pct=21,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=342, die_sides=1, implicit_target_a=63, implicit_target_b=31, radius_yards=15.0),
    ],
    spell_icon_id=2214,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 50); RealPointsPerLevel from rank1→level-60 slope (anchor rank 34864, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (48089, rank 7); MaxLevel set to 80. '
          'Priest Holy rework (HOLY.md "Baseline spell edits" / design doc §3): amount set to a flat 343 - checked this row\'s actual die_sides per PLAN §3.5 before typing the number, and it was NOT the default 1 (it was 37, a real min/max variance range inherited from the stock rank chain: 343-379). HOLY.md\'s own arithmetic ("base_points=342 if die_sides=1") assumes the default, which this row did not have - flattened die_sides to 1 (explicit override) here so the stated flat "343 + 0.4 SP" reads as a deterministic amount, consistent with how every other new spell in this pass (Holy Word: Serenity/Sanctify, Divine Star, Halo) is a flat number rather than a stock-style random range. points_per_level dropped (single-rank spells derive their level scaling from bonus_coefficients, not RealPointsPerLevel) - bonus_coefficients(direct=0.4) call below. Radius stays 15 yd (user override of the design doc\'s 30 yd, PLAN §1) - only the target-count/selection logic changes, in WP-B\'s C++ script.',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx3': 128, 'AttributesEx5': 4194304, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 50, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals up to 5 friendly party or raid members within $a1 yards of the target for $s1.', 'EffectBonusMultiplier_1': 0.4020000100135803, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftExclude': 134217728, 'ShapeshiftMask': 2147483648, 'SpellClassMask_1': 268435456, 'SpellClassSet': 6, 'SpellLevel': 50, 'SpellPriority': 50, 'SpellVisualID_1': 8253, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
bonus_coefficients(circle_of_healing_34861, direct=0.4)


vampiric_touch_34914 = spell(
    id=34914,
    name='Vampiric Touch',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=16,
    range_yards=30.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=6, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=89, points_per_level=3.0, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2213,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 50); RealPointsPerLevel from rank1→level-60 slope (anchor rank 34916, rank 2); coefficient/cast_time_ms/mana_cost_pct from max rank (48160, rank 5); MaxLevel set to 80',
    raw_overrides={'AttributesEx3': 67108864, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': "$s2 Shadow damage every $t2 seconds. Priest's party or raid members gain 1% of their maximum mana per 5 sec when the priest deals damage from Mind Blast.", 'BaseLevel': 50, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes $o2 Shadow damage over $d to your target and causes up to 10 party or raid members to gain 1% of their maximum mana per 5 sec when you deal damage from Mind Blast. In addition, if the Vampiric Touch is dispelled it will cause $*8;s2 damage to the afflicted target.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 0.4000000059604645, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 131072, 'SpellClassMask_2': 1024, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 50, 'SpellVisualID_1': 3582, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


penance_47540 = spell(
    id=47540,
    name='Penance',
    school=School.HOLY,
    attributes=536936704,
    category=1230,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=12000,
    mana_cost=0,
    mana_cost_pct=16,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=-1, implicit_target_a=25),
    ],
    spell_icon_id=2818,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 60); RealPointsPerLevel from rank1→top rank's own top level (84, chain has a gap at 60) slope (anchor rank 53007, rank 4); coefficient/cast_time_ms/mana_cost_pct from max rank (53007, rank 4); MaxLevel set to 80",
    raw_overrides={'AttributesEx': 268452996, 'AttributesEx4': 134217728, 'AttributesEx5': 8704, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31756, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Launches a volley of holy light at the target, causing $47666s1 Holy damage to an enemy, or $47750s1 healing to an ally instantly and every $47758t2 sec for $47758d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 160, 'SpellClassMask_2': 8388608, 'SpellClassSet': 6, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 10980, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


power_infusion_10060 = spell(
    id=10060,
    name='Power Infusion',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=16,
    range_yards=30.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=21, apply_aura=65, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=21, apply_aura=72, misc_value=126),
    ],
    spell_icon_id=1872,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Spell casting speed increased by $s1% and mana cost of spells reduced by $s2%.', 'BaseLevel': 40, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Infuses the target with power, increasing spell casting speed by $s1% and reducing the mana cost of all spells by $s2%.  Lasts $d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_2': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 2147483648, 'SpellClassMask_2': 536875008, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 40, 'SpellVisualID_1': 7553},
)


inner_focus_14751 = spell(
    id=14751,
    name='Inner Focus',
    school=School.NORMAL,
    dispel=DispelType.MAGIC,
    attributes=33882112,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COST),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CRITICAL_CHANCE),
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.CASTING_TIME),
    ],
    spell_icon_id=101,
    notes='Discipline rework (2,1) (docs/reworks/priest-disc-rework.md): Inner Focus stops being '
          '"your next spell, whatever it is" and becomes "your next Greater Heal, Flash Heal, Mind '
          'Blast or Power Word: Shield", with a different extra effect per spell. eff1 keeps its '
          'op (-100% mana cost) but is re-scoped from the stock everything-mask to exactly those '
          'four spells; eff2 keeps its op and +25% amount but is re-scoped to Greater Heal alone; '
          'eff3 is new - -50% cast time on Greater Heal and Mind Blast. Each SpellMod carries its '
          'classmask on ITS OWN letter (A = effect 1, B = effect 2, C = effect 3). The remaining '
          'two clauses are C++ (WP-B): Flash Heal\'s 100% crit is '
          'Priest::ApplySpellCritChanceMods, Mind Blast\'s 70% snare is '
          'spell_pri_inner_focus_mind_blast casting 200146, and Power Word: Shield\'s -10 sec '
          'Weakened Soul is in spell_pri_power_word_shield. ProcCharges stays 1 so the first '
          'matching cast consumes it.',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx3': 67108864, 'AttributesEx4': 524352, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next Greater Heal, Flash Heal, Mind Blast or Power Word: Shield is enhanced.', 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When activated, enhances your next Greater Heal, Flash Heal, Mind Blast or Power Word: Shield, reducing its mana cost by 100% and adding an additional effect.\n\nGreater Heal: reduces cast time by 50% and increases critical strike chance by 25%\nFlash Heal: increases critical strike chance to 100%\nMind Blast: reduces cast time by 50% and slows the target by 70% for 5 sec\nPower Word: Shield: reduces Weakened Soul duration by 10 sec', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': _masks.GREATER_HEAL | _masks.FLASH_HEAL | _masks.MIND_BLAST | _masks.PWS, 'EffectSpellClassMaskB_1': _masks.GREATER_HEAL, 'EffectSpellClassMaskC_1': _masks.GREATER_HEAL | _masks.MIND_BLAST, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'ShapeshiftMask': 134217728, 'SpellClassMask_2': 1073745920, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellVisualID_1': 4372},
)


shadowform_15473 = spell(
    id=15473,
    name='Shadowform',
    school=School.SHADOW,
    attributes=184877056,
    category=39,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=1500,
    mana_cost=0,
    mana_cost_pct=13,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=36, misc_value=28),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=79, misc_value=32),
        Effect(type=EffectType.APPLY_AURA, base_points=-16, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
    ],
    spell_icon_id=1552,
    notes='pulled from existing data',
    raw_overrides={'ActiveIconID': 55, 'AttributesEx': 131072, 'AttributesEx4': 2621440, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Shadow damage you deal increased by $s2%.  All damage you take reduced by $s3% and threat generated is reduced by $49868s1%. You may not cast Holy spells except Cure Disease and Abolish Disease.  Grants the periodic damage from your Shadow Word: Pain, Devouring Plague, and Vampiric Touch spells the ability to critically hit for $49868s2% increased damage and grants Devouring Plague and Vampiric Touch the ability to benefit from haste.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Assume a Shadowform, increasing your Shadow damage by $s2%, reducing all damage done to you by $s3% and threat generated by $49868s1%.  However, you may not cast Holy spells while in this form except Cure Disease and Abolish Disease.  Grants the periodic damage from your Shadow Word: Pain, Devouring Plague, and Vampiric Touch spells the ability to critically hit for $49868s2% increased damage and grants Devouring Plague and Vampiric Touch the ability to benefit from haste.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 2147483648, 'SpellClassMask_2': 2048, 'SpellClassSet': 6, 'SpellVisualID_1': 3619, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


silence_15487 = spell(
    id=15487,
    name='Silence',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    mechanic=Mechanic.SILENCE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=45000,
    category_cooldown_ms=0,
    mana_cost=225,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=6, apply_aura=AuraType.MOD_SILENCE),
    ],
    spell_icon_id=211,
    notes='Priest Shadow rework (SHADOW.md "Baseline spell edits" / design doc §5): moved out of the '
          'talent tree (541) into the base kit, trainer-taught at 30 like Shadow Word: Death '
          '(BaseLevel/SpellLevel added below; see trained_by() call). No other data changes - the '
          'stock SkillLineAbility row for skill 78 already exists.',
    raw_overrides={'AttributesEx2': 524288, 'AttributesEx6': 10485760, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Silenced.', 'BaseLevel': 30, 'SpellLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Silences the target, preventing them from casting spells for $d.  Non-player victim spellcasting is also interrupted for $32747d.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 134217728, 'SpellClassMask_2': 2101248, 'SpellClassSet': 6, 'SpellVisualID_1': 179},
)
# Trainer-taught at 30, same TrainerId/cost curve as Shadow Word: Death's own level-30 row
# (shadow_word_death_32379's trained_by() above: MoneyCost 10000 matches trainer 208's real
# level-30 rows).
trained_by(silence_15487, trainer_id=208, req_level=30, money_cost=10000)


pain_suppression_33206 = spell(
    id=33206,
    name='Pain Suppression',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=40.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-41, implicit_target_a=21, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=64, implicit_target_a=21, apply_aura=235),
    ],
    spell_icon_id=2178,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx5': 8, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'All damage taken reduced by $s1% and resistance to Dispel mechanics increased by $s2%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Instantly reduces a friendly target's threat by $44416s1%, reduces all damage taken by $s1% and increases resistance to Dispel mechanics by $s2% for $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskB_1': 45859183, 'EffectSpellClassMaskB_2': 5705, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 21, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 2147483648, 'SpellClassMask_2': 268439552, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellVisualID_1': 8039, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


dispersion_47585 = spell(
    id=47585,
    name='Dispersion',
    school=School.NORMAL,
    attributes=17039376,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-91, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=60),
    ],
    spell_icon_id=2875,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131104, 'AttributesEx5': 131080, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Reduces all damage by $s1%, and you regenerate $49766s1% mana every $60069t1 sec for $d.  Cannot attack or cast spells. Immune to snare and movement impairing effects.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You disperse into pure Shadow energy, reducing all damage taken by $47585s1%.  You are unable to attack or cast spells, but you regenerate $49766s1% mana every $60069t1 sec for $d. Dispersion can be cast while stunned, feared or silenced and clears all snare and movement impairing effects when cast, and makes you immune to them while dispersed.', 'EffectBasePoints_2': 5, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 262144, 'SpellClassMask_3': 1024, 'SpellClassSet': 6, 'SpellLevel': 60, 'SpellVisualID_1': 11005, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


guardian_spirit_47788 = spell(
    id=47788,
    name='Guardian Spirit',
    school=School.HOLY,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=40.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=21, apply_aura=AuraType.MOD_HEALING_PCT, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=21, apply_aura=69, misc_value=127),
    ],
    spell_icon_id=2873,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 524288, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increased healing received by $s1% and will prevent 1 killing blow.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Calls upon a guardian spirit to watch over the friendly target. The spirit increases the healing received by the target by $s1%, and also prevents the target from dying by sacrificing itself.  This sacrifice terminates the effect but heals the target of $s2% of their maximum health. Lasts $d.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ShapeshiftMask': 2281701376, 'SpellClassMask_1': 3221225472, 'SpellClassMask_3': 3072, 'SpellClassSet': 6, 'SpellLevel': 60, 'SpellVisualID_1': 12114},
)


psychic_horror_64044 = spell(
    id=64044,
    name='Psychic Horror',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=16,
    range_yards=30.0,
    duration_ms=3000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, mechanic=24, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
        Effect(type=EffectType.TRIGGER_SPELL, implicit_target_a=6, trigger_spell=64058),
    ],
    spell_icon_id=2847,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Horrified.', 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You terrify the target, causing them to tremble in horror for $d and drop their main hand and ranged weapons for $64058d.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectMechanic_3': 24, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_3': 8192, 'SpellClassSet': 6, 'SpellPriority': 50, 'SpellVisualID_1': 13757, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


# Priest baseline rework (docs/reworks/priest-new-spells.md) - Phase 1 shared spells, new baseline
# abilities every Priest spec gets. Fresh custom IDs minted from apps/dbc-tools/source/ids.yaml's
# reserved spell block (200000-209999), sequential from 200130 (the next free ID at the time this
# batch was written - see git history on ids.yaml's own comment for the block's rationale). Talent
# interactions (Aspiration's CD reduction, Guiding Star's Divine Star buff) are explicitly out of
# scope for this pass; so is Void Eruption's Shadow-spec "Generates 25 Madness" (Madness is a
# not-yet-built Shadow-spec resource, see docs/reworks/priest-shadow-rework.md) - only the shared
# baseline behavior ships here. C++ for all of these lives in a new
# src/server/scripts/Spells/spell_priest_new.cpp (kept separate from the existing, already-1400+
# line spell_priest.cpp) - see that file for the actual mechanics.
#
# Live playtest bug (2026-09-20): all 6 of these spells originally shipped with
# raw_overrides['AttributesEx'] = 4 (SPELL_ATTR1_IS_CHANNELED), copy-pasted from whatever template
# spell this batch started from. Confirmed harmless-but-wrong on 5 of them (Angelic Feather, Divine
# Star, Leap of Faith, Void Eruption - all cast_time_ms=0 with no duration_ms, so
# Spell::handle_immediate's IsChanneled()+duration>0 branch never fires) and a real, visible bug on
# the 6th (Halo - see its own notes) since its duration_ms=2000 made the server open a genuine
# 2-second channel. Removed from all 6 rather than just Halo, since none of them are meant to be
# channeled and leaving it on the other 5 is a landmine for whenever one of them gains a duration_ms
# (balance pass, talent interaction, etc.).

angelic_feather_200130 = spell(
    id=200130,
    name='Angelic Feather',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=30000,
    mana_cost_pct=4,
    range_yards=40.0,
    duration_ms=500,
    effects=[
        Effect(type=EffectType.PERSISTENT_AREA_AURA, base_points=0, implicit_target_a=29, implicit_target_b=29, apply_aura=AuraType.DUMMY, radius_yards=3.0),
        Effect(type=EffectType.TRIGGER_SPELL, trigger_spell=angelic_feather_place_200141.id),
    ],
    spell_icon_id=90100,
    notes='docs/reworks/priest-new-spells.md: "Places a feather at the target location, granting the first ally to walk through it 40% increased movement speed for 5 sec. Only 3 feathers can be placed at one time." Ground-targeted (Targets=64 raw_overrides below tells the client to show the ground-target cursor). Round-3 playtest fix (2026-09-20, "ring is STILL missing" after round 2\'s reorder): **split into two spells** - this row now carries ONLY the ring-drawing dummy (effect 0, unchanged from round 2: PERSISTENT_AREA_AURA/SPELL_AURA_DUMMY, base_points=0, radius_yards=3.0 to visually match the GO\'s own real 3-yard trigger, implicit_target_a=implicit_target_b=29/TARGET_DEST_DYNOBJ_ALLY) plus a new effect 1 (SPELL_EFFECT_TRIGGER_SPELL, cast-level, implicit_target_a left at 0/TARGET_NONE - SpellInfo.cpp\'s g_SpellEffectTargetTypes table lists SPELL_EFFECT_TRIGGER_SPELL as EFFECT_IMPLICIT_TARGET_NONE so this fires exactly once via Spell::EffectTriggerSpell\'s SPELL_EFFECT_HANDLE_LAUNCH branch, not per-unit) that triggers angelic_feather_place_200141 (priest_trigger_spells.py) - the actual SUMMON_OBJECT_SLOT1 effect that places the trap GO now lives entirely on that spell; see its own notes for why (dest-propagation mechanism, why Targets=64 matters there, why no C++ changes were needed). duration_ms=500 stays at the spell level, needed only for this row\'s own PERSISTENT_AREA_AURA dummy\'s DynamicObject to exist. Root-cause investigation for the split (2026-09-20): queried this project\'s own full client Spell.dbc (var/extractors/dbc/Spell.dbc, all 49839 rows, via lib.dbcfile.read_dbc) for every spell combining a SUMMON_OBJECT_SLOT1-4 effect (type 104-107) with a PERSISTENT_AREA_AURA effect (type 27) on the same spell ID - zero matches, out of 46 total stock spells using SUMMON_OBJECT_SLOT1-4 at all. Every real stock trap (Freezing Trap 1499, Immolation Trap 13795, etc.) uses Targets=0 (no ground-click reticle at all, placed at the caster\'s facing) rather than Targets=64 - the one Targets=64+ImplicitTargetA=87 exception found (Freezing Arrow 60202, a Cataclysm-era Hunter ground-target trap-shot, present in this client\'s Spell.dbc but with no confirmed live 3.3.5a usage - no creature/script in this repo references it) has EffectRadiusIndex_1=0 (no SpellRadius.dbc row for ID 0), i.e. no AoE radius at all for the client to size a ring from, so it isn\'t usable counter-evidence either way. This confirms round 2\'s "effect order" theory was never the real variable (reordering demonstrably did nothing, per the live playtest that prompted this round) and supports the working theory instead: the client\'s ground-target UI, on seeing a SUMMON_OBJECT_SLOT1-4 effect anywhere on the spell being aimed, switches to a "trap/object placement" cursor mode that never draws the AoE-radius ring overlay, regardless of what other effects coexist on the same spell ID or their ordering - matching that zero real Blizzard spell ever asks the client to do both at once. AttributesEx (0 on this spell vs nonzero on Blizzard/Flame Strike/PW:Barrier, flagged in the round-3 investigation brief as worth independently re-checking) was decoded bit-by-bit and ruled out: Blizzard\'s bits are SPELL_ATTR1_IS_CHANNELED/NO_REDIRECTION/NO_REFLECTION/NO_AURA_ICON, Flame Strike\'s and PW:Barrier\'s are NO_REDIRECTION/NO_REFLECTION - all either combat-mechanic flags or client-only aura-bar-visibility flags (SharedDefines.h), nothing ring-related, confirming the first-pass assessment independently. The GO itself, not this cast spell, is what actually grants the speed buff - see angelic_feather_buff_200131\'s own notes (priest_trigger_spells.py) for the trap-triggering mechanism and why it needs no proximity-check C++ of its own. spell_pri_angelic_feather (spell_priest_new.cpp) enforces "only 3 feathers at once" and stays registered on THIS spell (200130), not the new 200141 - see 200141\'s own notes for why the split doesn\'t break that ordering and why no C++ changes were needed for this round.',
    raw_overrides={'Targets': 64, 'BaseLevel': 42, 'SpellLevel': 42, 'MaxLevel': 80, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Places a feather at the target location, granting the first ally to walk through it 40% increased movement speed for 5 sec.  Only 3 feathers can be placed at one time.', 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 6, 'SpellPriority': 50, 'SpellVisualID_1': 90011, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'SpellClassMask_3': _masks.ANGELIC_FEATHER},
)
scripted_by(angelic_feather_200130, 'spell_pri_angelic_feather')
# skill_line here is the Spellbook tab this spell shows under (docs/skilllineability-handoff.md -
# the same real-SkillLine mechanism already fixed for the Mage rework: Frost=6/Fire=8/Arcane=237).
# This whole new-spells batch originally used skill_line=202 for all 6 spells, which isn't a Priest
# skill line at all - 202 is Engineering's real SkillLine.dbc ID (confirmed by reading the live
# client's SkillLine.dbc), a coincidental collision with Priest's Holy TalentTab.dbc ID (also 202,
# priest_talents.py's holy_202_tab) - hence every one of these spells showing under "General"
# instead of its intended spec tab. Verified real Priest SkillLine IDs the same way: Discipline=613,
# Holy=56, Shadow=78 (Divine Hymn 64843/64844's own untouched stock rows already carry SkillLine=56
# - Holy - confirming this reading).
skill_line_ability(id=30411, skill_line=56, spell_id=angelic_feather_200130.id, class_mask=16)  # Holy
# TrainerId 208 is the live Priest trainer (confirmed via lib/trainer_state.py's
# load_trainer_index().trainer_problems() - see devouring_plague_2944's own trained_by() comment for
# the dead-TrainerId-11 finding this project's existing priest spells all shared). Every genuinely
# new spell in this batch needs its own binding, same as this project's other reworks do for new
# spells (e.g. Fire Mage's Meteor, trainer_id=212). MoneyCost 16000 extrapolated from this trainer's
# real level-30/32/34 rows (~500c/level past 30) - first-pass estimate.
trained_by(angelic_feather_200130, trainer_id=208, req_level=42, money_cost=16000)


power_word_barrier_200132 = spell(
    id=200132,
    name='Power Word: Barrier',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=120000,
    mana_cost_pct=10,
    range_yards=40.0,
    radius_yards=10.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.PERSISTENT_AREA_AURA, base_points=-21, implicit_target_a=29, implicit_target_b=29, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, radius_yards=10.0),
        Effect(type=EffectType.PERSISTENT_AREA_AURA, base_points=99, implicit_target_a=29, implicit_target_b=29, apply_aura=149, radius_yards=10.0),
    ],
    spell_icon_id=3837,
    notes='docs/reworks/priest-new-spells.md: "Summons a holy barrier to protect all allies at the target location for 10 sec, reducing all damage taken by 20% and preventing damage from delaying spellcasting." Fully data-driven, no C++ needed at all - two PERSISTENT_AREA_AURA effects on one dest-target spell share a single DynamicObject/Aura zone (Spell::EffectPersistentAA, SpellEffects.cpp), so both land as one ground zone: effect 0 is MOD_DAMAGE_PERCENT_TAKEN (base_points=-21, stored -1 convention, for -20%); effect 1 is SPELL_AURA_REDUCE_PUSHBACK (apply_aura=149, SpellAuraDefines.h) at amount 100 (base_points=99, stored -1 convention) - confirmed read directly in Spell::Delayed (Spell.cpp): delayReduce>=100 fully suppresses cast-pushback for anyone standing in the zone, exactly matching "preventing damage from delaying spellcasting". implicit_target_a=29 (TARGET_DEST_DYNOBJ_ALLY, same target type Death and Decay/43265 uses for its own enemy-side equivalent, 28) both selects the ground-target reticle (raw_overrides Targets=64) and scopes the zone to allies only. Zone radius: the design doc doesn\'t give one - defaulted to 10 yds (retail\'s own value), flagged as playtest-tunable. spell_icon_id 3837 (Spell_Holy_PowerWordBarrier, apps/dbc-tools/var/spell_icon_names.csv) is the real spell\'s own stock icon - no icon mining needed for this one. SpellVisualID_1=90017 (patch_priest_vfx_models.py, SV_POWER_WORD_BARRIER) wraps genuine stock 3.3.5a client data - SpellVisualKit 12286 (BaseEffect=5211 "Power Word: Barrier Base" -> Spells\\Priest_PowerWardBarrier.mdx, a real Blizzard-authored dome model simply never wired to a live spell in vanilla WotLK) is reused completely untouched; no file extraction needed for this one, unlike the other 5 new spells. Two live playtest bugs (2026-09-20), both fixed: (1) originally set SpellVisualID_1 straight to stock 13210, which wires kit 12286 in as its ChannelKit - wrong slot for a non-channeled SPELL_EFFECT_PERSISTENT_AREA_AURA spell (confirmed against Death and Decay/Blizzard/Rain of Fire/Frost Trap Aura\'s own stock rows, which all use PersistentAreaKit for their ground-zone visual, never ChannelKit) - so the dome never rendered. Fixed by minting 90017, a fresh row pointing the same untouched kit 12286 at PersistentAreaKit instead (never hand-edit the shared stock row itself). (2) implicit_target_b was left at its 0 default on both effects - DynObjAura::FillTargetMap (SpellAuras.cpp) branches on TargetB, not TargetA, to decide whether a persistent-area aura\'s per-tick scan searches for friendly or enemy units; with TargetB unset it fell through to an enemy-only search (Unit::_IsValidAttackTarget), so a player standing in their own barrier could never actually receive the buff. Fixed by adding implicit_target_b=29 (TARGET_DEST_DYNOBJ_ALLY) to both effects, matching every real stock "stand in me for a friendly buff" persistent-area spell (Anti-Magic Barrier 52918, Toasty Fire 62821, Shield of the Blue 45848/47314, etc.). Live playtest bug #3 (2026-09-20): "the buff for Power Word: Barrier has no description" when hovering the aura icon on the buff bar while standing in the zone - NOT a missing/stale Description_Lang_enUS (that field was already correct in both the pending SQL and the deployed client patch-Z.mpq\'s own Spell.dbc, confirmed byte-for-byte). Root cause: Description_Lang and AuraDescription_Lang are two independent client-read string fields (both \'x\'/read_as_string in dbcfmt.py) for two different tooltip surfaces - Description is the spellbook/cast-bar tooltip, AuraDescription is what the buff-bar icon tooltip actually reads, and the client does NOT fall back from one to the other when the latter is empty. Confirmed against this project\'s own stock base DBC (var/extractors/dbc/Spell.dbc): every real buff/HoT spell sets a distinct, shorter AuraDescription alongside its longer Description (Renew 139: Description "Heals the target for $<total> over $d." vs AuraDescription "Healing $s1 damage every $t1 seconds."; Anti-Magic Zone 50461, the closest stock analog to this spell - a ground-target PERSISTENT_AREA_AURA buff zone - likewise has a distinct AuraDescription "Absorbs $50461s1% of spell damage." separate from its longer Description). This row never set AuraDescription_Lang at all, so the buff-bar tooltip had nothing to read. Divine Star (200133) and Halo (200135), whose spellbook/cast-bar descriptions the user confirmed look correct, aren\'t counter-evidence: neither applies a lasting buff to allies the way this spell does (Divine Star has no aura at all; Halo\'s aura is self-only), so neither one\'s buff-bar tooltip was ever exercised by that playtest. Fixed by adding AuraDescription_Lang_Mask=16712190 and a short AuraDescription_Lang_enUS ("Reduces damage taken by 20% and prevents damage from delaying spellcasting.") mirroring the stock convention of a condensed one-line summary of the zone\'s effect.',
    raw_overrides={'Targets': 64, 'BaseLevel': 60, 'SpellLevel': 60, 'MaxLevel': 80, 'AttributesEx': 136, 'AttributesEx5': 512, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Reduces damage taken by 20% and prevents damage from delaying spellcasting.', 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a holy barrier to protect all allies at the target location for $d, reducing all damage taken by 20% and preventing damage from delaying spellcasting.', 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 6, 'SpellPriority': 50, 'SpellVisualID_1': 90017, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'SpellClassMask_3': _masks.PW_BARRIER},
)
skill_line_ability(id=30412, skill_line=613, spell_id=power_word_barrier_200132.id, class_mask=16)  # Discipline
# See angelic_feather_200130's trained_by() comment for the TrainerId 208 rationale. MoneyCost
# 25000 matches divine_hymn_64843's own level-60 estimate (same level, same first-pass basis).
trained_by(power_word_barrier_200132, trainer_id=208, req_level=60, money_cost=25000)


divine_star_200133 = spell(
    id=200133,
    name='Divine Star',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=30000,
    mana_cost_pct=10,
    effects=[
        Effect(type=77, implicit_target_a=1),
    ],
    spell_icon_id=90101,
    notes='docs/reworks/priest-new-spells.md: "Throw a Divine Star forward 27 yds, healing allies in its path... and dealing... Holy damage to enemies. After reaching its destination, the Divine Star returns to you, healing allies and damaging enemies in its path again." Modeled directly on Frost Mage\'s Frozen Orb (mage_spells.py\'s frozen_orb_200007 + spell_mage.cpp\'s spell_mage_frozen_orb/npc_mage_frozen_orb) - the closest in-repo precedent for "summon a trigger creature that travels and pulses AoE, owner-attributed". SPELL_EFFECT_SCRIPT_EFFECT (type 77), self-targeted (implicit_target_a=1), instant, no damage/heal of its own - spell_pri_divine_star (spell_priest_new.cpp) summons npc_pri_divine_star (creature_template entry 300100, hand-written pending SQL) at the caster\'s position; that creature\'s own AI drives the out-and-back travel and, on each tick, has the OWNER cast divine_star_pulse_200134 (priest_trigger_spells.py) at whichever units it newly finds nearby - see that spell\'s own notes for the per-leg hit-dedup and the ">6 targets" healing falloff, both tracked in the creature AI rather than in DBC data. Differs from Frozen Orb in one real way: two separate legs (out, then back), each hitting a target at most once, rather than Frozen Orb\'s single halt-on-first-hit travel.',
    raw_overrides={'BaseLevel': 32, 'SpellLevel': 32, 'MaxLevel': 80, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Throw a Divine Star forward, healing allies in its path and dealing Holy damage to enemies.  After reaching its destination, the Divine Star returns to you, healing allies and damaging enemies in its path again.  Healing reduced beyond 6 targets.', 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6, 'SpellPriority': 50, 'SpellVisualID_1': 90012, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'SpellClassMask_3': _masks.DIVINE_STAR},
)
scripted_by(divine_star_200133, 'spell_pri_divine_star')
skill_line_ability(id=30413, skill_line=56, spell_id=divine_star_200133.id, class_mask=16)  # Holy
# See angelic_feather_200130's trained_by() comment for the TrainerId 208 rationale. MoneyCost
# 11000 matches this trainer's own real level-32 row (552, 11000c) exactly.
trained_by(divine_star_200133, trainer_id=208, req_level=32, money_cost=11000)


halo_200135 = spell(
    id=200135,
    name='Halo',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=60000,
    mana_cost_pct=30,
    duration_ms=2000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=100),
    ],
    spell_icon_id=90102,
    notes='docs/reworks/priest-new-spells.md: "Creates a ring of Holy energy around you that quickly expands to a 40 yd radius, healing allies for... and dealing... Holy damage to enemies." Deliberately NOT a summoned-creature spell (Frozen Orb\'s *travel-in-one-direction* half doesn\'t fit an all-directions-at-once ring; its *periodic-pulse-with-owner-attribution* half does): self-buff aura (PERIODIC_DUMMY, apply_aura=226) ticking every 100ms (amplitude=100) for the buff\'s duration_ms=2000 (total ring-expansion time to reach 40 yds - not specified in the design doc, flagged as playtest-tunable). spell_pri_halo (AuraScript on this spell, spell_priest_new.cpp), on OnEffectPeriodic, computes the ring\'s current radius from elapsed/total time, does a manual search for units newly crossed by the ring since the last tick, and casts halo_pulse_200136 (priest_trigger_spells.py) at each one individually - same explicit-single-unit-target "ally heals / enemy damages" idiom as Divine Star\'s pulse, chosen specifically to avoid native-AoE re-hit dedup problems (a naive fixed-radius AoE re-query every 100ms would re-hit everyone already inside the ring, not just those newly crossed by it). Live playtest bug (2026-09-20): originally shipped with AttributesEx=4 (SPELL_ATTR1_IS_CHANNELED) copy-pasted from this batch\'s other 5 new spells - harmless on those (no duration_ms, so Spell::handle_immediate\'s IsChanneled()+duration>0 branch never fires), but Halo\'s own duration_ms=2000 made the server actually open a 2-second channel (SendChannelStart), and the client then looked for this spell\'s (empty) ChannelKit instead of its correctly-authored PrecastKit/CastKit - explaining both "shows a channel bar" and "no animation plays" as one bug. Removed. '
          'Priest Holy rework (HOLY.md "Halo healing-taken" / design doc §3 "Halo"): tooltip gains the +10% healing-taken clause - design doc resolves the doc\'s own "unset variable" placeholder to a literal 10%, not a variable to compute. The buff itself (200173, MOD_HEALING_RECEIVED base 10, 10 s, scoped to this caster\'s own Holy heals via the SPELLFAMILY_PRIEST caster-GUID check native to SPELL_AURA_MOD_HEALING_RECEIVED - see Unit.cpp:9607-9613 - plus a classmask restricting it to priest heals, mirroring stock Grace\'s 47930 shape exactly) is declared in priest_trigger_spells.py; spell_pri_halo_pulse casting it on each target hit is WP-B\'s job (spell_priest_new.cpp).',
    raw_overrides={'BaseLevel': 52, 'SpellLevel': 52, 'MaxLevel': 80, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Creates a ring of Holy energy around you that quickly expands to a 40 yd radius, healing allies for $s1 and dealing $s1 Holy damage to enemies.  Allies healed by Halo take 10% increased healing from you for 10 sec.', 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6, 'SpellPriority': 50, 'SpellVisualID_1': 90014, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'SpellClassMask_3': _masks.HALO},
)
scripted_by(halo_200135, 'spell_pri_halo')
skill_line_ability(id=30414, skill_line=56, spell_id=halo_200135.id, class_mask=16)  # Holy
# See angelic_feather_200130's trained_by() comment for the TrainerId 208 rationale. MoneyCost
# 21000 extrapolated from this trainer's real level-30/32/34 rows (~500c/level past 30) -
# first-pass estimate.
trained_by(halo_200135, trainer_id=208, req_level=52, money_cost=21000)


leap_of_faith_200137 = spell(
    id=200137,
    name='Leap of Faith',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=60000,
    mana_cost_pct=1,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.DUMMY, implicit_target_a=21),
    ],
    spell_icon_id=90103,
    notes='docs/reworks/priest-new-spells.md: "Pulls the spirit of a party or raid member, instantly moving them directly in front of you." Modeled directly on DK Death Grip (spell_dk.cpp\'s spell_dk_death_grip, spells 49560/49576/57604): SPELL_EFFECT_DUMMY on an ally target (implicit_target_a=21, TARGET_UNIT_TARGET_ALLY - reversed from Death Grip\'s enemy target, since this pulls a friendly). spell_pri_leap_of_faith (spell_priest_new.cpp) computes a point near the caster (GetFirstCollisionPosition, facing-relative) and casts leap_of_faith_jump_200138 (priest_trigger_spells.py) on the target at that point, same target->CastSpell(destX, destY, destZ, jumpSpellId, true) call shape spell_dk_death_grip::HandleDummy uses - direction reversed (destination is near the *caster*, not the target\'s own explicit-target dest) so the ally lands offset from the priest rather than stacked on top of them.',
    raw_overrides={'BaseLevel': 46, 'SpellLevel': 46, 'MaxLevel': 80, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Pulls the spirit of a party or raid member, instantly moving them directly in front of you.', 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 6, 'SpellPriority': 50, 'SpellVisualID_1': 90016, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'SpellClassMask_3': _masks.LEAP_OF_FAITH},
)
scripted_by(leap_of_faith_200137, 'spell_pri_leap_of_faith')
skill_line_ability(id=30415, skill_line=56, spell_id=leap_of_faith_200137.id, class_mask=16)  # Holy
# See angelic_feather_200130's trained_by() comment for the TrainerId 208 rationale. MoneyCost
# 18000 extrapolated from this trainer's real level-30/32/34 rows (~500c/level past 30) -
# first-pass estimate.
trained_by(leap_of_faith_200137, trainer_id=208, req_level=46, money_cost=18000)


void_eruption_200139 = spell(
    id=200139,
    name='Void Eruption',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=45000,
    mana_cost_pct=4,
    range_yards=30.0,
    radius_yards=10.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=299, implicit_target_a=16, radius_yards=10.0),
        Effect(type=EffectType.TRIGGER_SPELL, implicit_target_a=1, trigger_spell=void_eruption_buff_200140.id),
    ],
    spell_icon_id=90104,
    notes='docs/reworks/priest-new-spells.md: "Releases an explosive blast of pure void energy, causing Shadow damage to up to 10 enemies within 10 yards of your target. The power drawn from the Void increases your periodic Shadow damage by 10% for 10 sec, with the duration increased by 0.5 sec for each enemy hit. While in Shadowform this spell also applies Shadow Word: Pain to all enemies hit." Baseline behavior only this pass, per the user\'s explicit scope call - Shadow spec\'s "Generates 25 Madness" (priest-shadow-rework.md) is deferred to whenever the Shadow resource system itself gets built. Effect 0: SCHOOL_DAMAGE, dest-area-enemy (implicit_target_a=16, matches Frozen Orb Pulse\'s own dest-area-enemy target), 10 yd radius; base_points=299 (stored -1 convention, ~300 damage - the design doc gives no explicit number, this is a first-pass placeholder in line with other level-40 Priest AoE damage, flagged as playtest-tunable). The "up to 10 enemies" cap is enforced in spell_pri_void_eruption (spell_priest_new.cpp) via OnObjectAreaTargetSelect trimming the hit list, not a DBC field. Effect 1: TRIGGER_SPELL, self, applying void_eruption_buff_200140 ("Voidform", priest_trigger_spells.py) - see that spell\'s own notes for the periodic-Shadow-damage-%-boost hook (PriestMechanics.h/.cpp) and the duration-extension/Shadow-Word:-Pain-application logic (both spell_pri_void_eruption).',
    raw_overrides={'BaseLevel': 40, 'SpellLevel': 40, 'MaxLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Releases an explosive blast of pure void energy, causing Shadow damage to up to 10 enemies within 10 yards of your target.  The power drawn from the Void increases your periodic Shadow damage by 10% for 10 sec, with the duration increased by 0.5 sec for each enemy hit.  While in Shadowform this spell also applies Shadow Word: Pain to all enemies hit.  Generates 12 Madness.', 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 6, 'SpellPriority': 50, 'SpellVisualID_1': 90015, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'SpellClassMask_3': _masks.VOID_ERUPTION},
)
# Priest Shadow rework (SHADOW.md "Baseline spell edits"): tooltip now states "Generates 12
# Madness" - visible units of the internal 25 (PLAN §1's display transform, visible=floor(internal/2)).
# The actual AddMadness(25, VoidEruption) call is WP-B's (spell_pri_void_eruption AfterCast).
scripted_by(void_eruption_200139, 'spell_pri_void_eruption')
skill_line_ability(id=30416, skill_line=78, spell_id=void_eruption_200139.id, class_mask=16)  # Shadow
# See angelic_feather_200130's trained_by() comment for the TrainerId 208 rationale. MoneyCost
# 15000 extrapolated from this trainer's real level-30/32/34 rows (~500c/level past 30) -
# first-pass estimate.
trained_by(void_eruption_200139, trainer_id=208, req_level=40, money_cost=15000)


# =====================================================================================
# Priest Discipline rework (docs/reworks/priest-disc-rework.md,
# .agents/plans/priest-rework/priest-rework.DISC.md)
# =====================================================================================

# --- (10,1) Spirit Shell -----------------------------------------------------------
# The one player-castable new spell of the Discipline pass. Instant, 1 min cooldown, 5%
# base mana, self-buff: while it is up, Priest::TryConvertHealToSpiritShell (PriestMechanics,
# called from Spell::DoAllEffectOnTarget's heal branch) turns each direct heal from Flash
# Heal / Greater Heal / Binding Heal / Prayer of Healing / Penance's heal bolt into an
# absorb (spirit_shell_absorb_200167) instead. The single DUMMY effect is only the marker
# that hook checks for. dword-3 bit 21 (_masks.SPIRIT_SHELL) is what lets Aspiration's
# cooldown SpellMod see it (PLAN §4.4).
spirit_shell_200166 = spell(
    id=200166,
    name='Spirit Shell',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=60000,
    mana_cost_pct=5,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        ApplyAura(AuraType.DUMMY, base_points=0, implicit_target_a=1),
    ],
    spell_icon_id=1804,
    notes='docs/reworks/priest-disc-rework.md, "Spirit Shell": "For 15 sec, your direct healing '
          'spells no longer heal. Instead they create an absorption shield on the target for the '
          'amount that would have been healed." The conversion list is fixed in PLAN §1 (Flash '
          'Heal, Greater Heal, Binding Heal, Prayer of Healing, Penance heal bolts - NOT Renew, '
          'Prayer of Mending, Circle of Healing, Divine Hymn, Halo, Divine Star, Holy Nova, Holy '
          'Words or Desperate Prayer) and lives in Priest::TryConvertHealToSpiritShell, not here. '
          'Absorb cap (60% of the target\'s max health), the Improved Power Word: Shield r3 '
          'Mastery multiplier and the "no Divine Aegis while Spirit Shell is active" rule are all '
          'in that same hook plus spell_pri_divine_aegis. Icon 1804 '
          '(Spell_Holy_GreaterBlessingofSanctuary) is a stock icon not otherwise used by any '
          'Discipline talent. A mined Ascension icon (ability_priest_angelicbulwark, custom id '
          '90105) was tried and rendered as a blank talent-frame slot in-game for reasons not '
          'conclusively diagnosed (DBC rows, packed file bytes, and manifest all verified correct '
          'both client- and server-side; reverted rather than keep chasing it - see '
          'docs/bugs-and-fixes.md).',
    raw_overrides={'BaseLevel': 80, 'SpellLevel': 80, 'MaxLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'For $d, your direct healing spells no longer heal.  Instead they create an absorption shield on the target for the amount that would have been healed.  Spirit Shell absorbs last 15 sec and are capped at 60% of the target\'s maximum health.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Direct heals create an absorption shield instead of healing.', 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_3': _masks.SPIRIT_SHELL, 'SpellClassSet': 6, 'SpellPriority': 50, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
# No skill_line_ability() call here on purpose: Spirit Shell is TALENT-granted, so its
# SkillLineAbility row (30417) is derived by granted_by_talent(player_castable=True, ...)
# in priest_talents.py, which is also what keeps it in the Discipline spellbook tab
# (discipline_201_tab.skill_line = 613). See lib/dsl/registry.py's granted_by_talent
# docstring and docs/skilllineability-handoff.md.


# --- spell_script_names bindings for the Discipline C++ pass -------------------------
# Every one of these binds an EXISTING stock spell (no row edit of its own) to a script
# class WP-B writes in src/server/scripts/Spells/spell_priest_disc.cpp. Exact positive
# ids, one call per spell - never the spell_script_names table's negative
# "-<id> = this and every rank" shorthand (source/classes/README.md).
scripted_by(mind_blast_8092, 'spell_pri_inner_focus_mind_blast')   # (2,1) Inner Focus: Mind Blast slow
scripted_by(dispel_magic_527, 'spell_pri_absolution')              # (3,0) Absolution
scripted_by(mass_dispel_32375, 'spell_pri_absolution')             # (3,0) Absolution - friendly half
# 32592 (bare id) is 32375's own TRIGGER_SPELL effect - the hostile purge half, no source/ Spell object.
scripted_by(32592, 'spell_pri_absolution')                         # (3,0) Absolution - hostile half
scripted_by(flash_heal_2061, 'spell_pri_improved_flash_heal_capstone')   # (6,2) capstone
scripted_by(power_infusion_10060, 'spell_pri_aspiration_power_infusion')  # (7,2) capstone


# =====================================================================================
# Priest Holy rework (docs/reworks/priest-holy-rework.md,
# .agents/plans/priest-rework/priest-rework.HOLY.md) - the 4 new player-castable Holy Word
# spells + Apotheosis. All four are TALENT-granted (60016/60017/60021/60022 in priest_talents.py),
# so - same convention as Spirit Shell (60010) above - none of them get a manual
# skill_line_ability() call here: player_castable=True + skill_line_ability_ids on their
# granted_by_talent() call derives the SkillLineAbility row (30418-30421) that keeps them in the
# Holy spellbook tab (holy_202_tab.skill_line=56, set in the Disc pass). No trained_by() either -
# these aren't trainer-taught.
# =====================================================================================

holy_word_serenity_200197 = spell(
    id=200197,
    name='Holy Word: Serenity',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=60000,
    mana_cost_pct=12,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=499, die_sides=1, implicit_target_a=21),
    ],
    spell_icon_id=90106,
    notes='HOLY.md §2/§"ID map": instant single-friendly heal, 60 s cooldown, 12% base mana, 500 + '
          '1.4 SP (base_points=499, stored -1 convention; bonus_coefficients(direct=1.4) below). '
          'TARGET_UNIT_TARGET_ALLY (21, SharedDefines.h) for "single friendly target". Reuses '
          'Halo\'s mined icon (90102) as a stand-in Holy Word icon pending dedicated icon mining '
          '(follow-up pass, per PLAN §7 runbook - icons/VFX are mined only after mechanics are '
          'verified). dword-3 bit 23 (_masks.HW_SERENITY) is its own family-flag identity, read by '
          'Divine Providence/Echo of Light/Apotheosis\'s classmask-scoped SpellMods and by the '
          'Serendipity capstone\'s cooldown-reduction script (HasAura/ModifySpellCooldown, not '
          'classmask - the family flag exists for the SpellMod consumers instead).',
    raw_overrides={'BaseLevel': 10, 'SpellLevel': 10, 'MaxLevel': 80, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly heals a friendly target for $s1.', 'EquippedItemClass': -1, 'InterruptFlags': 0, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 6, 'SpellPriority': 50, 'SpellVisualID_1': 280, 'SpellClassMask_3': _masks.HW_SERENITY},
)
bonus_coefficients(holy_word_serenity_200197, direct=1.4)
scripted_by(holy_word_serenity_200197, 'spell_pri_echo_of_light_heal')  # (8,3) Echo of Light


holy_word_sanctify_200198 = spell(
    id=200198,
    name='Holy Word: Sanctify',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=60000,
    mana_cost_pct=20,
    range_yards=40.0,
    radius_yards=8.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=299, die_sides=1, implicit_target_a=31, radius_yards=8.0),
    ],
    spell_icon_id=90107,
    notes='HOLY.md §2/§"ID map": instant ground-targeted AoE heal, 60 s cooldown, 20% base mana, '
          '300 + 0.6 SP per target (base_points=299, stored -1 convention; '
          'bonus_coefficients(direct=0.6) below), 8 yd radius. Ground-target: raw_overrides '
          'Targets=64 (TARGET_FLAG_DEST_LOCATION, client-side reticle flag) same as Angelic '
          'Feather (200130) and Power Word: Barrier (200132) use for their own ground-click '
          'spells. Implicit target TARGET_UNIT_DEST_AREA_ALLY (31, SharedDefines.h - the same '
          'enum Circle of Healing\'s own effect_2 already uses for "area allies around a dest '
          'point") heals allies around wherever the reticle is placed; no separate "select the '
          'dest" effect is needed the way PW:Barrier\'s PERSISTENT_AREA_AURA pair needs TargetA '
          '=TargetB=29, because a direct HEAL effect (not a persistent-aura zone) reads the cast\'s '
          'own dest target directly. No exact stock or in-repo precedent for "ground-target, '
          'direct (non-aura) AoE heal" was found via grep - flagged as a best-effort construction '
          'from the two closest precedents (PW:Barrier\'s ground-click plumbing, CoH\'s dest-area-'
          'ally implicit target) rather than a byte-for-byte copy of an existing row; verify the '
          'reticle actually appears in a live playtest. Falloff beyond 5 targets '
          '(sqrt(5/n) per target) is WP-B\'s job in spell_pri_holy_word_sanctify. dword-3 bit 24 '
          '(_masks.HW_SANCTIFY) is its own family-flag identity (same rationale as Serenity above).',
    raw_overrides={'Targets': 64, 'BaseLevel': 10, 'SpellLevel': 10, 'MaxLevel': 80, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals up to 5 friendly targets within $a1 yards of the target location for $s1.  Healing is reduced beyond 5 targets.', 'EquippedItemClass': -1, 'InterruptFlags': 0, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 6, 'SpellPriority': 50, 'SpellVisualID_1': 280, 'SpellClassMask_3': _masks.HW_SANCTIFY},
)
bonus_coefficients(holy_word_sanctify_200198, direct=0.6)
scripted_by(holy_word_sanctify_200198, 'spell_pri_holy_word_sanctify')
scripted_by(holy_word_sanctify_200198, 'spell_pri_echo_of_light_heal')  # (8,3) Echo of Light


holy_word_chastise_200223 = spell(
    id=200223,
    name='Holy Word: Chastise',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=60000,
    mana_cost_pct=10,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=399, die_sides=1, implicit_target_a=6),
        Effect(type=EffectType.TRIGGER_SPELL, implicit_target_a=1, trigger_spell=200224),
    ],
    spell_icon_id=90108,
    notes='HOLY.md §2/§"ID map": instant single-enemy Holy damage, 60 s cooldown, 10% base mana, '
          '30 yd. Damage amount is a playtest guess per design doc §7 - PLAN §1\'s resolved call '
          'is "400 + 1.0 SP first pass" (base_points=399, stored -1 convention; '
          'bonus_coefficients(direct=1.0) below). effect_2 TRIGGER_SPELL (self) applies the '
          '10 sec Smite/Holy Fire damage buff (200224, priest_trigger_spells.py). dword-3 bit 25 '
          '(_masks.HW_CHASTISE) is its own family-flag identity (same rationale as Serenity above). '
          "Reuses Void Eruption's mined icon (90104) as a stand-in pending dedicated icon mining "
          '(follow-up pass, per PLAN §7 runbook - same convention as Serenity/Sanctify reusing '
          "Halo's 90102; talent-tooltip-audit noted the reuse, this comment documents it rather "
          'than treating it as an oversight).',
    raw_overrides={'BaseLevel': 10, 'SpellLevel': 10, 'MaxLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Smites an enemy for $s1 Holy damage and increases the damage of your next Smite or Holy Fire spell by 30% for 10 sec.', 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 6, 'SpellPriority': 50, 'SpellClassMask_3': _masks.HW_CHASTISE},
)
bonus_coefficients(holy_word_chastise_200223, direct=1.0)
scripted_by(holy_word_chastise_200223, 'spell_pri_echo_of_light_damage')  # (8,3) Echo of Light


apotheosis_200225 = spell(
    id=200225,
    name='Apotheosis',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=180000,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.MOD_HEALING_DONE_PERCENT),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=108, misc_value=SpellModOp.COST),
    ],
    spell_icon_id=90109,
    notes='HOLY.md §2/§"ID map" (10,1): instant self-buff, 180 s cooldown, no cost, 20 s. eff1 '
          'MOD_HEALING_DONE_PERCENT (136) +10% (base_points=9, stored -1 convention); eff2 '
          'MOD_DAMAGE_PERCENT_DONE (79) misc_value=2 (Holy school mask) +30% (base_points=29) - '
          'design doc §2 "school-wide rather than Priest-only" (PLAN §8 accepted risk #1: this is '
          'deliberate, a Classless build can buy the same window). eff3 ADD_PCT_MODIFIER (108) '
          'misc_value=SpellModOp.COST (14) -100% (base_points=-101), scoped via '
          'EffectSpellClassMaskC_3 (letter C = effect index 3, per the load-bearing letter/number '
          'gotcha) to HW_SERENITY|HW_SANCTIFY|HW_CHASTISE so only the three Holy Words go free. '
          'dword-3 bit 26 (_masks.APOTHEOSIS) is its own family-flag identity, unused by any '
          'classmask-scoped SpellMod so far but minted per PLAN §4.4\'s table for consistency with '
          'the other three new spells. Serendipity\'s x3 Holy Word cooldown-reduction rate reads '
          'this buff by HasAura(200225), not by classmask - WP-B\'s job (spell_pri_holy_word_engine). '
          "Reuses Void Eruption's mined icon (90104) as a stand-in pending dedicated icon mining "
          '(follow-up pass, per PLAN §7 runbook - same convention as Serenity/Sanctify/Chastise).',
    raw_overrides={'BaseLevel': 10, 'SpellLevel': 10, 'MaxLevel': 80, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'For $d, your healing done is increased by 10%, your Holy school damage done is increased by 30%, your Holy Words cost no mana, and Serendipity\'s Holy Word cooldown reduction is tripled.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Healing and Holy damage done increased; Holy Words cost no mana.', 'EquippedItemClass': -1, 'InterruptFlags': 0, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6, 'SpellPriority': 50, 'SpellClassMask_3': _masks.APOTHEOSIS, 'EffectSpellClassMaskC_3': _masks.HW_SERENITY | _masks.HW_SANCTIFY | _masks.HW_CHASTISE},
)


# --- spell_script_names bindings for the Holy C++ pass (HOLY.md's "Script" column) --------------
# spell_pri_holy_concentration_extend (6,0 Holy Concentration): AfterCast on the 4 spells that can
# roll the Renew-extension chance.
scripted_by(greater_heal_2060, 'spell_pri_holy_concentration_extend')
scripted_by(flash_heal_2061, 'spell_pri_holy_concentration_extend')
scripted_by(binding_heal_32546, 'spell_pri_holy_concentration_extend')
scripted_by(circle_of_healing_34861, 'spell_pri_holy_concentration_extend')
# spell_pri_renew_cast (2,1 Answered Prayers): AfterCast on Renew itself.
scripted_by(renew_139, 'spell_pri_renew_cast')
# spell_pri_holy_word_engine (7,2 Serendipity capstone): AfterCast on every spell whose cast can
# charge a Holy Word's cooldown reduction.
scripted_by(greater_heal_2060, 'spell_pri_holy_word_engine')
scripted_by(flash_heal_2061, 'spell_pri_holy_word_engine')
scripted_by(binding_heal_32546, 'spell_pri_holy_word_engine')
scripted_by(prayer_of_healing_596, 'spell_pri_holy_word_engine')
scripted_by(circle_of_healing_34861, 'spell_pri_holy_word_engine')
scripted_by(renew_139, 'spell_pri_holy_word_engine')
scripted_by(smite_585, 'spell_pri_holy_word_engine')
scripted_by(holy_fire_14914, 'spell_pri_holy_word_engine')


# --- Priest Shadow rework: player-castable new spells (SHADOW.md's "ID map") ---------------------
# Call of the Void (200248) and Surrender to Madness (200269) both have a real cast_time_ms/
# cooldown_ms and aren't marked passive, so looks_player_castable() would hard-error without
# player_castable=True on their granted_by_talent() calls (priest_talents.py) - see
# source/classes/README.md.

call_of_the_void_200248 = spell(
    id=200248,
    name='Call of the Void',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=60000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.DUMMY, implicit_target_a=1),
    ],
    spell_icon_id=90104,
    notes='Priest Shadow rework (SHADOW.md (4,0) / ID map): NEW talent-granted active, repurposes '
          '542 (was Improved Psychic Scream at 2,0). Instant, 60 s cooldown, no cost, self. eff1 is a '
          'real (non-aura) SPELL_EFFECT_DUMMY - script-driven entirely by spell_pri_call_of_the_void '
          "(WP-B: CheckCast locks it out while Surrender to Madness (200269) is up; OnCast consumes "
          'all Madness and casts the buff, 200249, with BP0 = consumed/2). dword3 bit 27 '
          '(_masks.CALL_OF_THE_VOID) is its own family-flag identity. SkillLineAbility 30422 is '
          "derived automatically by granted_by_talent's player_castable=True (priest_talents.py) - "
          "no separate skill_line_ability() call needed. Reuses Void Eruption's mined icon (90104) "
          'as a stand-in pending dedicated icon mining (follow-up pass, per PLAN §7 runbook).',
    raw_overrides={'BaseLevel': 40, 'SpellLevel': 40, 'MaxLevel': 80, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "You generate Madness, up to 250. Your Mind Flay damage and your Tentacles of Madness' Mind Flay damage generate Madness, and your Mind Blast generates more. Consume all Madness, increasing the damage of your Tentacles of Madness by 1% per Madness consumed for 15 sec.", 'EquippedItemClass': -1, 'InterruptFlags': 0, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6, 'SpellPriority': 50, 'SpellClassMask_3': _masks.CALL_OF_THE_VOID},
)
scripted_by(call_of_the_void_200248, 'spell_pri_call_of_the_void')


surrender_to_madness_200269 = spell(
    id=200269,
    name='Surrender to Madness',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=180000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=120000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=1000),
        Effect(type=EffectType.DUMMY, implicit_target_a=1),
    ],
    spell_icon_id=90104,
    notes='Priest Shadow rework (SHADOW.md (10,1) / ID map): NEW talent, minted id 60025 - '
          '**no `depends_on`** (PLAN §1/SHADOW.md top-of-file: overrides the design doc\'s own '
          '"real prerequisite arrow" note and design doc §4.5 - a 6-tier diagonal arrow from Call '
          'of the Void (4,0) cannot render in TalentFrame_DrawLines; Surrender\'s own CheckCast gate '
          '(GetMadness()==0 -> fail) already makes it useless without Call of the Void). Instant, '
          '180 s cooldown, self, 120 s duration (spell_pri_surrender_to_madness ends it early once '
          'Madness reaches 0 or combat drops). eff1 PERIODIC_DUMMY (226), 1 s amplitude - drives the '
          "drain-per-second OnPeriodic tick. eff2 is a real (non-aura) SPELL_EFFECT_DUMMY, unused by "
          'the script directly (declared per the ID map\'s effect shape). dword3 bit 28 '
          '(_masks.SURRENDER) is its own family-flag identity. SkillLineAbility 30423 is derived '
          "automatically by granted_by_talent's player_castable=True (priest_talents.py). Reuses "
          "Void Eruption's mined icon (90104) as a stand-in pending dedicated icon mining.",
    raw_overrides={'BaseLevel': 50, 'SpellLevel': 50, 'MaxLevel': 80, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You surrender to the voices. Your Madness drains at 6.5 per second, increasing by 0.5 per second each second, and can no longer be spent. Your own Mind Flay and Mind Blast generate triple Madness. While active, your Tentacles of Madness do not expire, and every Shadow Word: Pain and Mind Flay damage event summons one, ignoring the shared cooldown. When your Madness reaches 0, Surrender ends and your Tentacles of Madness are destroyed. If no enemies remain in combat with you or your party, Surrender ends immediately and you do not suffer Sundered Mind.', 'EquippedItemClass': -1, 'InterruptFlags': 0, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 6, 'SpellPriority': 50, 'SpellClassMask_3': _masks.SURRENDER},
)
scripted_by(surrender_to_madness_200269, 'spell_pri_surrender_to_madness')
