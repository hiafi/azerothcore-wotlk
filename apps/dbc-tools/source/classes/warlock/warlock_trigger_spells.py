"""
Warlock - spells that are never directly cast - proc/periodic-tick effects, trigger_spell targets, hidden talent-rank buffs, etc..

Split from a single source/classes/warlock.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .warlock_...` below) resolve.
"""

from lib.dsl import AuraType, DispelType, Effect, EffectType, Mechanic, PowerType, RANGE_SELF, School
from lib.dsl.registry import bonus_coefficients, linked_spell, procs_on, scripted_by, spell, spell_group, spell_group_rule, unbind_script, unlink_spell
from . import _masks as m


life_tap_1454 = spell(
    id=1454,
    name='Life Tap',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.HEALTH,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=26, points_per_level=26.66216216216216, implicit_target_a=1, radius_yards=50000.0),
    ],
    spell_icon_id=208,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 6); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 8 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx2': 33554432, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 6, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Converts ${$m1+$SPI*1.5} health into ${$m1*$<mult>+$SPS*.5*$<mult>} mana.  Spell power increases the amount of mana returned.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 262144, 'SpellClassSet': 5, 'SpellDescriptionVariableID': 175, 'SpellLevel': 6, 'SpellVisualID_1': 1225, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
scripted_by(life_tap_1454, 'spell_warl_life_tap_affliction')
unbind_script(-1454, 'spell_warl_life_tap')


fire_shield_2947 = spell(
    id=2947,
    name='Fire Shield',
    school=School.FIRE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=180000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, points_per_level=0.42424242424242425, implicit_target_a=57, apply_aura=15),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=57, apply_aura=143, misc_value=4),
    ],
    spell_icon_id=16,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 14); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 7 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 524288, 'AttributesEx6': 4, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Causes $s1 Fire damage to attacker when struck.', 'BaseLevel': 14, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Surrounds the friendly party or raid target in a shield of fire, making every strike against the target cause $s1 Fire damage to the attacker.  Lasts $d.  The caster cannot cast Fire Shield on himself.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 8388608, 'SpellClassSet': 5, 'SpellLevel': 14, 'SpellPriority': 50, 'SpellVisualID_1': 289, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


hellfire_effect_5857 = spell(
    id=5857,
    name='Hellfire Effect',
    school=School.FIRE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=82, points_per_level=7.4, implicit_target_a=18, implicit_target_b=16, radius_yards=10.0),
    ],
    spell_icon_id=937,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 30); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 136, 'AttributesEx2': 1610612736, 'AttributesEx3': 33554432, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Ignites the area surrounding the caster, causing $1949s2 Fire damage to $ghimself:herself; and $5857s1 Fire damage to all nearby enemies every $1949t2 sec.  Lasts $1949d.', 'EffectBonusMultiplier_1': 0.14300000667572021, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 64, 'SpellClassSet': 5, 'SpellLevel': 30, 'SpellVisualID_1': 781},
)


blood_pact_6307 = spell(
    id=6307,
    name='Blood Pact',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=65, base_points=19, points_per_level=17.236842105263158, implicit_target_a=1, apply_aura=230, misc_value=2, radius_yards=30.0),
    ],
    spell_icon_id=541,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 4); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 7 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'ActiveIconID': 122, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases health by $s1.', 'BaseLevel': 4, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases party and raid members' health by $s1.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 8388608, 'SpellClassSet': 5, 'SpellLevel': 4, 'SpellVisualID_1': 799},
)


consume_shadows_17767 = spell(
    id=17767,
    name='Consume Shadows',
    school=School.SHADOW,
    attributes=268435456,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=104, points_per_level=17.019354835633308, implicit_target_a=1, apply_aura=AuraType.PERIODIC_HEAL, amplitude=2000),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=54501),
    ],
    spell_icon_id=207,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 18); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131136, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Heals $s1 damage every $t1 seconds and greatly increasing stealth detection to all nearby friendly targets within $54501a yards.', 'BaseLevel': 18, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31772, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The Voidwalker consumes nearby shadows to bolster its form, recovering $o1 health over $d and greatly increasing stealth detection to all nearby friendly targets within $54501a yards. Cannot be used while in combat.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 33554432, 'SpellClassSet': 5, 'SpellLevel': 18, 'SpellVisualID_1': 4779, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


seed_of_corruption_27285 = spell(
    id=27285,
    name='Seed of Corruption',
    school=School.SHADOW,
    attributes=8388608,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=813, points_per_level=18.5, die_sides=181, implicit_target_a=16, radius_yards=15.0),
    ],
    spell_icon_id=1932,
    notes='warlock-rework AFFLICTION §4.1 B8 items 3/4b: coefficient restored to 0.2129 (was 0.286, its spell_bonus_data row was deleted); base rebased via B3 (V60=1110 min) with learn level moved 70->44 -> 814-994@44, 1110-1290@60, 1480-1660@80. SpellClassMask_2 keeps 0x10 (detonation, unaffected by the B16 Seed DoT rebit).',
    raw_overrides={'AttributesEx2': 4, 'AttributesEx3': 1, 'AttributesEx5': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 44, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Imbeds a demon seed in the enemy target, causing $27243o1 Shadow damage over $27243d.  When the target takes $27243s2 total damage or dies, the seed will inflict $27285s1 Shadow damage to all enemies within $27285a1 yards of the target.', 'EffectBonusMultiplier_1': 0.2129, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 32784, 'SpellClassSet': 5, 'SpellLevel': 44, 'SpellVisualID_1': 7682, 'Targets': 64},
)
scripted_by(seed_of_corruption_27285, 'spell_warl_seed_of_corruption_detonation_affliction')


improved_death_coil_30049 = spell(
    id=30049,
    name='Improved Death Coil',
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
        Effect(type=EffectType.APPLY_AURA, base_points=9, points_per_level=0.3333333333333333, implicit_target_a=1, apply_aura=108, misc_value=27),
    ],
    spell_icon_id=88,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the healing effect of your Death Coil spell by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 524288, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 5},
)


destructive_soul_30251 = spell(
    id=30251,
    name='Destructive Soul',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=34, points_per_level=0.5932203389830508, implicit_target_a=1, apply_aura=108, misc_value=9),
    ],
    spell_icon_id=1984,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your Destruction spells a $s1% chance to not lose casting time when you take damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 997, 'EffectSpellClassMaskA_2': 192, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5, 'SpellLevel': 1, 'SpellPriority': 50},
)


rain_of_fire_42223 = spell(
    id=42223,
    name='Rain of Fire',
    school=School.FIRE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, points_per_level=0.0, implicit_target_a=87, implicit_target_b=16, radius_yards=8.0),
    ],
    spell_icon_id=547,
    notes="warlock-rework DESTRUCTION §4.2 (B18 + R5 + C5, spell_warl_rain_of_fire_tick / AuraScript on 5740, WP-B): bp/ppl zeroed - the AuraScript passes the whole snapshot as CustomSpellValues BP0 every tick (Spell::SetSpellValue already applies the die_sides convention, so the script passes the intended value, not value-1). implicit_target_a 76 (DEST_CHANNEL_TARGET, no longer exists once RoF isn't a channel) -> 87 (TARGET_DEST_DEST); B 16 and range 100 kept. AttributesEx3 |= 0x20000000 (IGNORE_CASTER_MODIFIERS - fixed per-tick base; blocks every SpellMod except SPELLMOD_DURATION, taken-side mods unaffected). EffectBonusMultiplier_1 -> 0.1716 (documentation only, inert under the attribute). No SUPPRESS_CASTER_PROCS - RoF hits must still proc Molten Skin and Hellstorm (their spell_proc rows carry PROC_ATTR_TRIGGERED_CAN_PROC).",
    raw_overrides={'AttributesEx': 136, 'AttributesEx2': 1073741824, 'AttributesEx3': 1610612736, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Calls down a fiery rain to burn enemies in the area of effect for ${$42223m1*4} Fire damage over $5740d.', 'EffectBonusMultiplier_1': 0.1716, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 135, 'SpellClassMask_1': 32, 'SpellClassSet': 5, 'SpellLevel': 20, 'SpellPriority': 50, 'SpellVisualID_1': 10045, 'StartRecoveryCategory': 133},
)
scripted_by(rain_of_fire_42223, 'spell_warl_rain_of_fire_tick')


seed_of_corruption_43991 = spell(
    id=43991,
    name='Seed of Corruption',
    school=School.SHADOW,
    attributes=8388608,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=1109, points_per_level=52.3, die_sides=181, implicit_target_a=31, radius_yards=15.0),
    ],
    spell_icon_id=1932,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 70); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 3 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx2': 4, 'AttributesEx3': 65537, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 70, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712188, 'EffectBonusMultiplier_1': 0.21400000154972076, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 32784, 'SpellClassSet': 5, 'SpellLevel': 70, 'SpellVisualID_1': 7682, 'Targets': 64},
)


kindling_soul_47261 = spell(
    id=47261,
    name='Kindling Soul',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=47426),
        Effect(type=EffectType.APPLY_AURA, base_points=4, points_per_level=0.08333333333333333, implicit_target_a=1, apply_aura=174, misc_value=36),
    ],
    spell_icon_id=1920,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spell damage is increased by $s2% of your Spirit, and your spell criticals increase your Spirit by $47426s1% for 10 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_2': 4, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 81920, 'RangeIndex': 1, 'SpellClassSet': 5},
)


torture_47263 = spell(
    id=47263,
    name='Torture',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=33151),
    ],
    spell_icon_id=34,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'After you critically strike with a Shadow spell, your next Searing Pain or Immolate spells have a @% chance to become instant cast. This ability has a 20 second cooldown.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 25, 'ProcTypeMask': 81920, 'RangeIndex': 1, 'SpellClassSet': 5},
)


fel_intelligence_54424 = spell(
    id=54424,
    name='Fel Intelligence',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=65, base_points=11, points_per_level=0.7516666666294137, implicit_target_a=1, apply_aura=AuraType.MOD_STAT, misc_value=3, radius_yards=100.0),
        Effect(type=65, base_points=17, points_per_level=0.9599999999627471, implicit_target_a=1, apply_aura=AuraType.MOD_STAT, misc_value=4, radius_yards=100.0),
    ],
    spell_icon_id=1940,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 32); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'ActiveIconID': 122, 'AttributesEx': 1024, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases Intellect by $s1 and Spirit by $s2.', 'BaseLevel': 32, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases party and raid members Intellect by $s1 and Spirit by $s2.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 33554432, 'SpellClassSet': 5, 'SpellLevel': 32, 'SpellVisualID_1': 799},
)


dark_pact_18220 = spell(
    id=18220,
    name='Dark Pact',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.POWER_DRAIN, base_points=304, points_per_level=22.375, implicit_target_a=5),
    ],
    spell_icon_id=154,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 40); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 33554436, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 40, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Drains $s1 of your summoned demon's Mana, returning 100% to you.", 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 2147483648, 'SpellClassMask_3': 32768, 'SpellClassSet': 5, 'SpellLevel': 40, 'SpellVisualID_1': 827, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetCreatureType': 4},
)


cataclysm_17778 = spell(
    id=17778,
    name='Cataclysm',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=108, misc_value=0),
    ],
    spell_icon_id=1197,
    notes='warlock-rework DESTRUCTION §6 (1,2): eff0 misc COST(14) -> DAMAGE(0), mask -> CATACLYSM_SPELLS (RoF/Hellfire, Shadowfury, Inferno Effect, HoG); stock B mask (vestigial - no effect 2) cleared.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage of your Rain of Fire, Hellfire, Inferno, Hand of Gul'dan and Shadowfury by $s1%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.CATACLYSM_SPELLS[0], 'EffectSpellClassMaskA_2': m.CATACLYSM_SPELLS[1], 'EffectSpellClassMaskA_3': m.CATACLYSM_SPELLS[2], 'EffectSpellClassMaskB_1': 0, 'EffectSpellClassMaskB_2': 0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


cataclysm_17779 = spell(
    id=17779,
    name='Cataclysm',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=108, misc_value=0),
    ],
    spell_icon_id=1197,
    notes='warlock-rework DESTRUCTION §6 (1,2): see rank 1s note.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage of your Rain of Fire, Hellfire, Inferno, Hand of Gul'dan and Shadowfury by $s1%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.CATACLYSM_SPELLS[0], 'EffectSpellClassMaskA_2': m.CATACLYSM_SPELLS[1], 'EffectSpellClassMaskA_3': m.CATACLYSM_SPELLS[2], 'EffectSpellClassMaskB_1': 0, 'EffectSpellClassMaskB_2': 0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


cataclysm_17780 = spell(
    id=17780,
    name='Cataclysm',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=17, implicit_target_a=1, apply_aura=108, misc_value=0),
    ],
    spell_icon_id=1197,
    notes='warlock-rework DESTRUCTION §6 (1,2): see rank 1s note. Tooltip amended by S3 to insert "Summon Infernal, " after "Inferno, " (DEMONOLOGY §11 Q8) - not yet done here.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage of your Rain of Fire, Hellfire, Inferno, Hand of Gul'dan and Shadowfury by $s1%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.CATACLYSM_SPELLS[0], 'EffectSpellClassMaskA_2': m.CATACLYSM_SPELLS[1], 'EffectSpellClassMaskA_3': m.CATACLYSM_SPELLS[2], 'EffectSpellClassMaskB_1': 0, 'EffectSpellClassMaskB_2': 0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


fel_concentration_17783 = spell(
    id=17783,
    name='Fel Concentration',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL),
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=1, apply_aura=AuraType.REDUCE_PUSHBACK),
    ],
    spell_icon_id=76,
    notes='warlock-rework AFFLICTION §6 (2,1): rewritten from a single pushback-reduction SpellMod into two plain player auras (haste + pushback reduction on every damaging cast, not classmask-scoped) - no classmask needed on either effect.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell, ranged and melee haste by $s1%.  Reduces pushback suffered from damaging attacks while casting by $s2%.\n\n|cFF9D9D9DCapstone Bonus: Your periodic magic damage heals you for 20% of the damage done while casting any damaging spell. This heal cannot exceed 5% of your maximum health.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


fel_concentration_17784 = spell(
    id=17784,
    name='Fel Concentration',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL),
        Effect(type=EffectType.APPLY_AURA, base_points=65, implicit_target_a=1, apply_aura=AuraType.REDUCE_PUSHBACK),
    ],
    spell_icon_id=76,
    notes='warlock-rework AFFLICTION §6 (2,1)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell, ranged and melee haste by $s1%.  Reduces pushback suffered from damaging attacks while casting by $s2%.\n\n|cFF9D9D9DCapstone Bonus: Your periodic magic damage heals you for 20% of the damage done while casting any damaging spell. This heal cannot exceed 5% of your maximum health.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


fel_concentration_17785 = spell(
    id=17785,
    name='Fel Concentration',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.REDUCE_PUSHBACK),
    ],
    spell_icon_id=76,
    notes='warlock-rework AFFLICTION §6 (2,1) capstone: rank 3 also carries the periodic-damage-while-casting self heal (Warlock::LeechTalent::FelConcentration, spell_warl_fel_concentration_capstone on this id) - data only here, C++ is WP-B.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell, ranged and melee haste by $s1%.  Reduces pushback suffered from damaging attacks while casting by $s2%.\n\nCapstone Bonus: Your periodic magic damage heals you for 20% of the damage done while casting any damaging spell. This heal cannot exceed 5% of your maximum health.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
scripted_by(fel_concentration_17785, 'spell_warl_fel_concentration_capstone')
procs_on(fel_concentration_17785, proc_flags=m.PROC_FLAG_DONE_PERIODIC, school_mask=126, spell_type_mask=m.PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=m.PROC_SPELL_PHASE_HIT, chance=100, cooldown_ms=0)


bane_17788 = spell(
    id=17788,
    name='Bane',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, base_points=-6, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=169,
    notes='warlock-rework DESTRUCTION §6 (0,2): eff0 rewritten from a cast-time SpellMod to ADD_FLAT_MODIFIER CRITICAL_CHANCE (+2/4/6%), eff1 to ADD_PCT_MODIFIER COST (-5/-10/-15%), both A/B = BANE_SPELLS (SB, Immolate; Incinerate, Soul Fire, Shadowflame, Chaos Bolt; Shadowflame DoT; Hand of Gul\'dan).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the critical strike chance of Shadow Bolt, Incinerate, Chaos Bolt, Immolate, Hand of Gul'dan, Soul Fire and Shadowflame by $s1% and reduces the mana cost of these spells by $s2%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.BANE_SPELLS[0], 'EffectSpellClassMaskA_2': m.BANE_SPELLS[1], 'EffectSpellClassMaskA_3': m.BANE_SPELLS[2], 'EffectSpellClassMaskB_1': m.BANE_SPELLS[0], 'EffectSpellClassMaskB_2': m.BANE_SPELLS[1], 'EffectSpellClassMaskB_3': m.BANE_SPELLS[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


bane_17789 = spell(
    id=17789,
    name='Bane',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=107, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=169,
    notes='warlock-rework DESTRUCTION §6 (0,2): see rank 1s note.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the critical strike chance of Shadow Bolt, Incinerate, Chaos Bolt, Immolate, Hand of Gul'dan, Soul Fire and Shadowflame by $s1% and reduces the mana cost of these spells by $s2%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.BANE_SPELLS[0], 'EffectSpellClassMaskA_2': m.BANE_SPELLS[1], 'EffectSpellClassMaskA_3': m.BANE_SPELLS[2], 'EffectSpellClassMaskB_1': m.BANE_SPELLS[0], 'EffectSpellClassMaskB_2': m.BANE_SPELLS[1], 'EffectSpellClassMaskB_3': m.BANE_SPELLS[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


bane_17790 = spell(
    id=17790,
    name='Bane',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=107, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, base_points=-16, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=169,
    notes='warlock-rework DESTRUCTION §6 (0,2): see rank 1s note.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the critical strike chance of Shadow Bolt, Incinerate, Chaos Bolt, Immolate, Hand of Gul'dan, Soul Fire and Shadowflame by $s1% and reduces the mana cost of these spells by $s2%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.BANE_SPELLS[0], 'EffectSpellClassMaskA_2': m.BANE_SPELLS[1], 'EffectSpellClassMaskA_3': m.BANE_SPELLS[2], 'EffectSpellClassMaskB_1': m.BANE_SPELLS[0], 'EffectSpellClassMaskB_2': m.BANE_SPELLS[1], 'EffectSpellClassMaskB_3': m.BANE_SPELLS[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


bane_17791 = spell(
    id=17791,
    name='Bane',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-401, implicit_target_a=1, apply_aura=107, misc_value=10),
        Effect(type=EffectType.APPLY_AURA, base_points=-1601, implicit_target_a=1, apply_aura=107, misc_value=10),
    ],
    spell_icon_id=169,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the casting time of your Shadow Bolt. Chaos Bolt and Immolate spells by $/1000;S1 sec and your Soul Fire spell by $/1000;S2 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 5, 'EffectSpellClassMaskA_2': 131072, 'EffectSpellClassMaskB_2': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


bane_17792 = spell(
    id=17792,
    name='Bane',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-501, implicit_target_a=1, apply_aura=107, misc_value=10),
        Effect(type=EffectType.APPLY_AURA, base_points=-2001, implicit_target_a=1, apply_aura=107, misc_value=10),
    ],
    spell_icon_id=169,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the casting time of your Shadow Bolt. Chaos Bolt and Immolate spells by $/1000;S1 sec and your Soul Fire spell by $/1000;S2 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 5, 'EffectSpellClassMaskA_2': 131072, 'EffectSpellClassMaskB_2': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_shadow_bolt_17793 = spell(
    id=17793,
    name='Improved Shadow Bolt',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=17800),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=213,
    notes='warlock-rework DESTRUCTION §6 (0,1): eff1 bp 1/3/5 -> 4/9/14 (5/10/15%), mask widened to Shadow Bolt + Incinerate (B_2 = INCINERATE); ProcChance 20/40/60 -> 33/66/100; -18095 stock proc row replaced (§8).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Shadow Bolt and Incinerate by $s2%. Your Shadow Bolt and Incinerate have a $h% chance to cause your target to be vulnerable to spell damage, increasing spell critical strike chance against that target by $17800s1%. Effect lasts $17800d. Does not stack with other similar effects.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': m.SHADOW_BOLT, 'EffectSpellClassMaskB_2': m.INCINERATE, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 33, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_shadow_bolt_17796 = spell(
    id=17796,
    name='Improved Shadow Bolt',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=17800),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=213,
    notes='warlock-rework DESTRUCTION §6 (0,1): see rank 1s note.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Shadow Bolt and Incinerate by $s2%. Your Shadow Bolt and Incinerate have a $h% chance to cause your target to be vulnerable to spell damage, increasing spell critical strike chance against that target by $17800s1%. Effect lasts $17800d. Does not stack with other similar effects.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': m.SHADOW_BOLT, 'EffectSpellClassMaskB_2': m.INCINERATE, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 66, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_shadow_bolt_17801 = spell(
    id=17801,
    name='Improved Shadow Bolt',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=17800),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=213,
    notes='warlock-rework DESTRUCTION §6 (0,1): see rank 1s note.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Shadow Bolt and Incinerate by $s2%. Your Shadow Bolt and Incinerate have a $h% chance to cause your target to be vulnerable to spell damage, increasing spell critical strike chance against that target by $17800s1%. Effect lasts $17800d. Does not stack with other similar effects.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': m.SHADOW_BOLT, 'EffectSpellClassMaskB_2': m.INCINERATE, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 5},
)
procs_on(-17793, proc_flags=m.PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG, family_name=5, family_mask=(m.SHADOW_BOLT, m.INCINERATE, 0), spell_type_mask=m.PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=m.PROC_SPELL_PHASE_HIT, chance=0, cooldown_ms=0)


improved_shadow_bolt_17802 = spell(
    id=17802,
    name='Improved Shadow Bolt',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=17800),
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=213,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Shadow Bolt spell by $s2%, and your Shadow Bolt has a $h% chance to cause your target to be vulnerable to spell damage, increasing spell critical strike chance against that target by $17800s1%. Effect lasts $17800d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 80, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_shadow_bolt_17803 = spell(
    id=17803,
    name='Improved Shadow Bolt',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=17800),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=213,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Shadow Bolt spell by $s2%, and your Shadow Bolt has a $h% chance to cause your target to be vulnerable to spell damage, increasing spell critical strike chance against that target by $17800s1%. Effect lasts $17800d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 5},
)


soul_siphon_17804 = spell(
    id=17804,
    name='Soul Siphon',
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
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=0),
    ],
    spell_icon_id=546,
    notes='warlock-rework AFFLICTION §6 (2,3): eff2 (cap %, was the C3 stock-hardcode key OVERRIDE_CLASS_SCRIPTS misc 4992/4993) made inert -> plain DUMMY read by Warlock::GetSoulSiphonMultiplier; masks cleared (no SpellMod left on this talent).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount drained by your Drain Life and Drain Soul spells, and the damage of your Phantom Singularity, by an additional $s1% for each of your Affliction damage over time effects on the target, to a maximum of $s2% additional effect.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


soul_siphon_17805 = spell(
    id=17805,
    name='Soul Siphon',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=23, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=0),
    ],
    spell_icon_id=546,
    notes='warlock-rework AFFLICTION §6 (2,3): see rank 1s note.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount drained by your Drain Life and Drain Soul spells, and the damage of your Phantom Singularity, by an additional $s1% for each of your Affliction damage over time effects on the target, to a maximum of $s2% additional effect.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_corruption_17810 = spell(
    id=17810,
    name='Improved Corruption',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=313,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Corruption by $s1%, and increases the critical strike chance of your Seed of Corruption by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2, 'EffectSpellClassMaskB_2': 32768, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_corruption_17811 = spell(
    id=17811,
    name='Improved Corruption',
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
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=313,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Corruption by $s1%, and increases the critical strike chance of your Seed of Corruption by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2, 'EffectSpellClassMaskB_2': 32768, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_corruption_17812 = spell(
    id=17812,
    name='Improved Corruption',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=313,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Corruption by $s1%, and increases the critical strike chance of your Seed of Corruption by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2, 'EffectSpellClassMaskB_2': 32768, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_corruption_17813 = spell(
    id=17813,
    name='Improved Corruption',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=313,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Corruption by $s1%, and increases the critical strike chance of your Seed of Corruption by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2, 'EffectSpellClassMaskB_2': 32768, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_corruption_17814 = spell(
    id=17814,
    name='Improved Corruption',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=313,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Corruption by $s1%, and increases the critical strike chance of your Seed of Corruption by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2, 'EffectSpellClassMaskB_2': 32768, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_immolate_17815 = spell(
    id=17815,
    name='Improved Immolate',
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
    spell_icon_id=31,
    notes='warlock-rework DESTRUCTION §6 (4,3): data unchanged; tooltip gets the grey capstone preview (PLAN §2 format - r3 carries the real capstone).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Immolate spell by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Your Immolate periodic damage has a 5% chance to erupt, dealing Fire damage to all enemies within 5 yards of the target that are in combat with you.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4, 'EffectSpellClassMaskB_1': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_immolate_17833 = spell(
    id=17833,
    name='Improved Immolate',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=31,
    notes='warlock-rework DESTRUCTION §6 (4,3): data unchanged; tooltip gets the grey capstone preview (PLAN §2 format).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Immolate spell by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Your Immolate periodic damage has a 5% chance to erupt, dealing Fire damage to all enemies within 5 yards of the target that are in combat with you.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4, 'EffectSpellClassMaskB_1': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_immolate_17834 = spell(
    id=17834,
    name='Improved Immolate',
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
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=31,
    notes='warlock-rework DESTRUCTION §6 (4,3): r3 eff2 aura 286 (ABILITY_PERIODIC_CRIT) -> DUMMY (proc carrier for the eruption capstone, §7.10); stale C_2 Conflagrate mask cleared. eff0/eff1 (damage/DOT %) unchanged.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Immolate spell by $s1%.\n\nCapstone Bonus: Your Immolate periodic damage has a 5% chance to erupt, dealing Fire damage to all enemies within 5 yards of the target that are in combat with you.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4, 'EffectSpellClassMaskB_1': 4, 'EffectSpellClassMaskC_2': 0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
scripted_by(improved_immolate_17834, 'spell_warl_improved_immolate_eruption')
procs_on(improved_immolate_17834, proc_flags=m.PROC_FLAG_DONE_PERIODIC, family_name=5, family_mask=(m.IMMOLATE, 0, 0), spell_type_mask=m.PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=m.PROC_SPELL_PHASE_HIT, chance=5, cooldown_ms=2000, disable_effects_mask=0x3)


destructive_reach_17917 = spell(
    id=17917,
    name='Destructive Reach',
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
        Effect(type=EffectType.APPLY_AURA, base_points=0, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=160,
    notes='warlock-rework DESTRUCTION §6 (3,1): both effects zeroed the SHARED §1.1 way (type -> APPLY_AURA DUMMY, bp 0, die_sides 0, masks cleared - a die-1 +1 SpellMod or a stale mask would otherwise still apply/leak). Range joins the shared Reach passives via linked_spell(17917, 200707, 2); capstone (r2) crit is a CanPrepare script (WP-B, §7.9).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of your damaging spells by 3 yards. This does not stack with other similar effects.\n\n|cFF9D9D9DCapstone Bonus: Increases your spell critical strike chance by 4% against enemies farther than 20 yards away.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 0, 'EffectSpellClassMaskA_2': 0, 'EffectSpellClassMaskB_1': 0, 'EffectSpellClassMaskB_2': 0, 'EffectSpellClassMaskB_3': 0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
linked_spell(17917, 200707, type=2)


destructive_reach_17918 = spell(
    id=17918,
    name='Destructive Reach',
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
        Effect(type=EffectType.APPLY_AURA, base_points=0, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=160,
    notes='warlock-rework DESTRUCTION §6 (3,1): r2, see rank 1s note. Capstone Bonus text on this (final) rank; the +4% crit approximation is Warlock::ApplyDestructiveReachCrit in the shared CanPrepare handler (WP-B, §7.9), helper spell 200991 (built here).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of your damaging spells by 6 yards. This does not stack with other similar effects.\n\nCapstone Bonus: Increases your spell critical strike chance by 4% against enemies farther than 20 yards away.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 0, 'EffectSpellClassMaskA_2': 0, 'EffectSpellClassMaskB_1': 0, 'EffectSpellClassMaskB_2': 0, 'EffectSpellClassMaskB_3': 0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
linked_spell(17918, 200708, type=2)


improved_searing_pain_17927 = spell(
    id=17927,
    name='Improved Searing Pain',
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
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=816,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Searing Pain spell by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 256, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_searing_pain_17929 = spell(
    id=17929,
    name='Improved Searing Pain',
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
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=816,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Searing Pain spell by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 256, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_searing_pain_17930 = spell(
    id=17930,
    name='Improved Searing Pain',
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
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=816,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Searing Pain spell by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 256, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


emberstorm_17954 = spell(
    id=17954,
    name='Emberstorm',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=0, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=37,
    notes='warlock-rework DESTRUCTION §6 (5,1): eff0/eff1 bp 2/5/8 -> 1/3/5 (2/4/6%), masks -> EMBERSTORM_DAMAGE/EMBERSTORM_DOT; eff2 (stock Incinerate cast-time SpellMod) zeroed the SHARED §1.1 way (type -> APPLY_AURA DUMMY, bp 0, die_sides 0, C masks cleared).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Fire spells by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Your Incinerate, Searing Pain, Scorch and Fireball casts reduce the remaining cooldown of Chaos Bolt by 1.5 sec. When an enemy dies while afflicted by your Shadowburn, the remaining cooldown of Chaos Bolt is reduced by 4 sec.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.EMBERSTORM_DAMAGE[0], 'EffectSpellClassMaskA_2': m.EMBERSTORM_DAMAGE[1], 'EffectSpellClassMaskA_3': m.EMBERSTORM_DAMAGE[2], 'EffectSpellClassMaskB_1': m.EMBERSTORM_DOT[0], 'EffectSpellClassMaskB_2': m.EMBERSTORM_DOT[1], 'EffectSpellClassMaskB_3': m.EMBERSTORM_DOT[2], 'EffectSpellClassMaskC_2': 0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


emberstorm_17955 = spell(
    id=17955,
    name='Emberstorm',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=0, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=37,
    notes='warlock-rework DESTRUCTION §6 (5,1): see rank 1s note.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Fire spells by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Your Incinerate, Searing Pain, Scorch and Fireball casts reduce the remaining cooldown of Chaos Bolt by 1.5 sec. When an enemy dies while afflicted by your Shadowburn, the remaining cooldown of Chaos Bolt is reduced by 4 sec.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.EMBERSTORM_DAMAGE[0], 'EffectSpellClassMaskA_2': m.EMBERSTORM_DAMAGE[1], 'EffectSpellClassMaskA_3': m.EMBERSTORM_DAMAGE[2], 'EffectSpellClassMaskB_1': m.EMBERSTORM_DOT[0], 'EffectSpellClassMaskB_2': m.EMBERSTORM_DOT[1], 'EffectSpellClassMaskB_3': m.EMBERSTORM_DOT[2], 'EffectSpellClassMaskC_2': 0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


emberstorm_17956 = spell(
    id=17956,
    name='Emberstorm',
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
        Effect(type=EffectType.APPLY_AURA, base_points=0, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=37,
    notes='warlock-rework DESTRUCTION §6 (5,1): r3, final rank - plain capstone text; capstone script is WarlockEmberstormCooldown (warlock_hooks.cpp, WP-B) + spell_warl_shadowburn_destruction (§7.8/§7.15).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Fire spells by $s1%.\n\nCapstone Bonus: Your Incinerate, Searing Pain, Scorch and Fireball casts reduce the remaining cooldown of Chaos Bolt by 1.5 sec. When an enemy dies while afflicted by your Shadowburn, the remaining cooldown of Chaos Bolt is reduced by 4 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.EMBERSTORM_DAMAGE[0], 'EffectSpellClassMaskA_2': m.EMBERSTORM_DAMAGE[1], 'EffectSpellClassMaskA_3': m.EMBERSTORM_DAMAGE[2], 'EffectSpellClassMaskB_1': m.EMBERSTORM_DOT[0], 'EffectSpellClassMaskB_2': m.EMBERSTORM_DOT[1], 'EffectSpellClassMaskB_3': m.EMBERSTORM_DOT[2], 'EffectSpellClassMaskC_2': 0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


emberstorm_17957 = spell(
    id=17957,
    name='Emberstorm',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=-201, implicit_target_a=1, apply_aura=107, misc_value=10),
    ],
    spell_icon_id=37,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Fire spells by $s1% and reduces the cast time of your Incinerate spell by ${$m3/-1000}.2 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 868, 'EffectSpellClassMaskA_2': 8519872, 'EffectSpellClassMaskB_1': 100, 'EffectSpellClassMaskB_2': 8388608, 'EffectSpellClassMaskB_3': 2, 'EffectSpellClassMaskC_2': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


emberstorm_17958 = spell(
    id=17958,
    name='Emberstorm',
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
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=-251, implicit_target_a=1, apply_aura=107, misc_value=10),
    ],
    spell_icon_id=37,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Fire spells by $s1% and reduces the cast time of your Incinerate spell by ${$m3/-1000}.2 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 868, 'EffectSpellClassMaskA_2': 8519872, 'EffectSpellClassMaskB_1': 100, 'EffectSpellClassMaskB_2': 8388608, 'EffectSpellClassMaskB_3': 2, 'EffectSpellClassMaskC_2': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


ruin_17959 = spell(
    id=17959,
    name='Ruin',
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
    spell_icon_id=234,
    notes='warlock-rework DESTRUCTION §6 (5,2), A1/A2 (SHARED §1.1): eff0 stock ADD_PCT_MODIFIER CRIT_DAMAGE_BONUS zeroed (type -> APPLY_AURA DUMMY, bp 0, die_sides 0, A masks cleared) and replaced by the shared crit-damage passive via linked_spell(17959, 200701, 2) - 165% at this rank.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spell critical strikes now deal 165% damage. This does not stack with other similar effects.\n\n|cFF9D9D9DCapstone Bonus: Increases your Fire and Shadow damage done by 3%. This effect is quadrupled against targets above 75% health.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 0, 'EffectSpellClassMaskA_2': 0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
linked_spell(17959, 200701, type=2)


pyroclasm_18073 = spell(
    id=18073,
    name='Pyroclasm',
    school=School.FIRE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=2189, trigger_spell=63243),
    ],
    spell_icon_id=1137,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you critically strike with Searing Pain, Scorch, or Conflagrate, your Fire and Shadow spell damage is increased by $63243s1% for $63243d.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 576, 'EffectSpellClassMaskA_2': 8388736, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 5},
)
scripted_by(pyroclasm_18073, 'spell_warl_pyroclasm')


nightfall_18094 = spell(
    id=18094,
    name='Nightfall',
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
    ],
    spell_icon_id=164,
    notes='warlock-rework AFFLICTION §6 (3,3) / §7.5: eff1 now carries the live Shadow Bolt damage bonus (5%, passed as BP2 by the Shadow Trance cast script); ProcChance raised 2->3.',
    raw_overrides={'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Corruption, Drain Life, Drain Soul and Shadowflame spells have a $h% chance for your next Shadow Bolt or Seed of Corruption to become an instant cast and consume 50% less mana.  This Shadow Bolt deals $s1% more damage.  This effect can only occur every 5 sec.\n\n|cFF9D9D9DCapstone Bonus: Your Shadow Bolt causes your Unstable Affliction on the target to instantly deal one tick of its periodic damage.|r', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 3, 'ProcTypeMask': 327680, 'RangeIndex': 1, 'SpellClassSet': 5, 'SpellLevel': 1},
)


nightfall_18095 = spell(
    id=18095,
    name='Nightfall',
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
    ],
    spell_icon_id=164,
    notes='warlock-rework AFFLICTION §6 (3,3): ProcChance raised 4->6.',
    raw_overrides={'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Corruption, Drain Life, Drain Soul and Shadowflame spells have a $h% chance for your next Shadow Bolt or Seed of Corruption to become an instant cast and consume 50% less mana.  This Shadow Bolt deals $s1% more damage.  This effect can only occur every 5 sec.\n\n|cFF9D9D9DCapstone Bonus: Your Shadow Bolt causes your Unstable Affliction on the target to instantly deal one tick of its periodic damage.|r', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 6, 'ProcTypeMask': 327680, 'RangeIndex': 1, 'SpellClassSet': 5, 'SpellLevel': 1},
)


nightfall_200766 = spell(
    id=200766,
    name='Nightfall',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=164,
    notes='warlock-rework AFFLICTION §6 (3,3): new rank 3 (talent 1002 rank count 2->3, PLAN §1); carries the "Unstable Affliction instant tick" capstone (spell_warl_shadow_bolt_affliction, §7.5).',
    raw_overrides={'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Corruption, Drain Life, Drain Soul and Shadowflame spells have a $h% chance for your next Shadow Bolt or Seed of Corruption to become an instant cast and consume 50% less mana.  This Shadow Bolt deals $s1% more damage.  This effect can only occur every 5 sec.\n\nCapstone Bonus: Your Shadow Bolt causes your Unstable Affliction on the target to instantly deal one tick of its periodic damage.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 9, 'ProcTypeMask': 327680, 'RangeIndex': 1, 'SpellClassSet': 5, 'SpellLevel': 1},
)
scripted_by(nightfall_18094, 'spell_warl_nightfall_affliction')
scripted_by(nightfall_18095, 'spell_warl_nightfall_affliction')
scripted_by(nightfall_200766, 'spell_warl_nightfall_affliction')
unbind_script(-18094, 'spell_warl_nightfall')
procs_on(-18094, proc_flags=0x50000, family_name=5, family_mask=m.NIGHTFALL_TRIGGER, spell_type_mask=1, spell_phase_mask=m.PROC_SPELL_PHASE_HIT, chance=0, cooldown_ms=5000)


pyroclasm_18096 = spell(
    id=18096,
    name='Pyroclasm',
    school=School.FIRE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=2188, trigger_spell=18093),
    ],
    spell_icon_id=1137,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you critically strike with Searing Pain, Scorch, or Conflagrate, your Fire and Shadow spell damage is increased by $18093s1% for $18093d.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 576, 'EffectSpellClassMaskA_2': 8388736, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 5},
)
scripted_by(pyroclasm_18096, 'spell_warl_pyroclasm')
procs_on(-18096, proc_flags=m.PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG, family_name=0, spell_type_mask=0, spell_phase_mask=m.PROC_SPELL_PHASE_HIT, hit_mask=m.PROC_HIT_CRITICAL, chance=100, cooldown_ms=0)


aftermath_18119 = spell(
    id=18119,
    name='Aftermath',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=18118),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=11,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the periodic damage done by your Immolate by $s2%, and your Conflagrate has a $h% chance to daze the target for $18118d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 5},
)


aftermath_18120 = spell(
    id=18120,
    name='Aftermath',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=18118),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=11,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the periodic damage done by your Immolate by $s2%, and your Conflagrate has a $h% chance to daze the target for $18118d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 5},
)


demonic_power_18126 = spell(
    id=18126,
    name='Demonic Power',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=107, misc_value=10),
        Effect(type=EffectType.APPLY_AURA, base_points=-3001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=0),
    ],
    spell_icon_id=18,
    notes='warlock-rework DESTRUCTION §6 (2,0): eff0 bp -251 -> -101 (-0.1s cast time, matches the design docs "0.1 sec"); eff1 unchanged (Lash of Pain CD -3s). New eff2 ADD_PCT_MODIFIER DAMAGE (SpellModOp.DAMAGE=0) bp 6 (+7%), C_1 = IMP_FIREBOLT (0x1000) - the "+7% Imps Firebolt damage" clause. Wild Imp Fel Firebolt 200824 side is scripted, Demonologys (S3) job (§0.1/§11 Q13 resolved (a)).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces the cooldown of your Succubus' Lash of Pain spell by $/1000;s2 sec. Reduces the cast time of your Imp's Firebolt and the Firebolt of your Wild Imps by $/-1000;s1 sec, and increases their damage by $s3%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskB_1': 8192, 'EffectSpellClassMaskC_1': m.IMP_FIREBOLT, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


demonic_power_18127 = spell(
    id=18127,
    name='Demonic Power',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-251, implicit_target_a=1, apply_aura=107, misc_value=10),
        Effect(type=EffectType.APPLY_AURA, base_points=-6001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=13, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=0),
    ],
    spell_icon_id=18,
    notes='warlock-rework DESTRUCTION §6 (2,0): r2, see rank 1s note - eff0 bp -501 -> -251 (-0.25s cast time), eff2 bp 13 (+14%).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces the cooldown of your Succubus' Lash of Pain spell by $/1000;s2 sec. Reduces the cast time of your Imp's Firebolt and the Firebolt of your Wild Imps by $/-1000;s1 sec, and increases their damage by $s3%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskB_1': 8192, 'EffectSpellClassMaskC_1': m.IMP_FIREBOLT, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


devastation_18130 = spell(
    id=18130,
    name='Devastation',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=678,
    notes='warlock-rework DESTRUCTION §6 (4,2): rank count 1->3 (200969/200970 are the new r2/r3). eff0 bp 4 -> 1 (2%), mask -> DESTRUCTION_SPELLS.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Destruction spells by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Your Incinerate casts have a 10% chance to trigger Chaotic Inferno, making your next Chaos Bolt instant. Lasts 15 sec.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.DESTRUCTION_SPELLS[0], 'EffectSpellClassMaskA_2': m.DESTRUCTION_SPELLS[1], 'EffectSpellClassMaskA_3': m.DESTRUCTION_SPELLS[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


devastation_200969 = spell(
    id=200969,
    name='Devastation',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=678,
    notes='warlock-rework DESTRUCTION §6 (4,2): new rank 2 (talent 981 rank count 1->3), clone of 18130 with bp 3 (4%).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Destruction spells by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Your Incinerate casts have a 10% chance to trigger Chaotic Inferno, making your next Chaos Bolt instant. Lasts 15 sec.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.DESTRUCTION_SPELLS[0], 'EffectSpellClassMaskA_2': m.DESTRUCTION_SPELLS[1], 'EffectSpellClassMaskA_3': m.DESTRUCTION_SPELLS[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


devastation_200970 = spell(
    id=200970,
    name='Devastation',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=107, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL),
    ],
    spell_icon_id=678,
    notes='warlock-rework DESTRUCTION §6 (4,2): new rank 3 (final), bp 5 (6%); eff1 PROC_TRIGGER_SPELL carrier for the Chaotic Inferno capstone (row in §8: DONE_SPELL_MAGIC_DMG_CLASS_NEG, fam 5 (0, 0x40, 0), CAST, chance 10). Plain capstone text (final rank).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Destruction spells by $s1%.\n\nCapstone Bonus: Your Incinerate casts have a 10% chance to trigger Chaotic Inferno, making your next Chaos Bolt instant. Lasts 15 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.DESTRUCTION_SPELLS[0], 'EffectSpellClassMaskA_2': m.DESTRUCTION_SPELLS[1], 'EffectSpellClassMaskA_3': m.DESTRUCTION_SPELLS[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
procs_on(devastation_200970, proc_flags=m.PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG, family_name=5, family_mask=(0, m.INCINERATE, 0), spell_type_mask=m.PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=m.PROC_SPELL_PHASE_CAST, chance=10, cooldown_ms=0, disable_effects_mask=0x1)


intensity_18135 = spell(
    id=18135,
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
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=108, misc_value=9),
    ],
    spell_icon_id=876,
    notes='warlock-rework DESTRUCTION §6 (3,0): eff0 bp 34 -> 49 (50%), mask -> DESTRUCTION_CAST_SPELLS.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the pushback suffered from damaging attacks while casting or channeling any Destruction spell by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Your Chaos Bolt and Conflagrate casts have a 15% chance to grant Intensity, increasing your haste by 15% for 8 sec.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.DESTRUCTION_CAST_SPELLS[0], 'EffectSpellClassMaskA_2': m.DESTRUCTION_CAST_SPELLS[1], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


intensity_18136 = spell(
    id=18136,
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
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=108, misc_value=9),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200988),
    ],
    spell_icon_id=876,
    notes='warlock-rework DESTRUCTION §6 (3,0): r2 final rank, eff0 bp 69 -> 99 (100%), mask -> DESTRUCTION_CAST_SPELLS; new eff1 PROC_TRIGGER_SPELL carrier for the Intensity-buff capstone proc (§8: fam 5 (0, 0x820000, 0), CAST, chance 15).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the pushback suffered from damaging attacks while casting or channeling any Destruction spell by $s1%.\n\nCapstone Bonus: Your Chaos Bolt and Conflagrate casts have a 15% chance to grant Intensity, increasing your haste by 15% for 8 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.DESTRUCTION_CAST_SPELLS[0], 'EffectSpellClassMaskA_2': m.DESTRUCTION_CAST_SPELLS[1], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
procs_on(intensity_18136, proc_flags=m.PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG, family_name=5, family_mask=(0, 0x820000, 0), spell_type_mask=0, spell_phase_mask=m.PROC_SPELL_PHASE_CAST, chance=15, cooldown_ms=0, disable_effects_mask=0x1)


suppression_18174 = spell(
    id=18174,
    name='Suppression',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=199, misc_value=36),
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=150,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your chance to hit with spells by $s1%, and reduces the mana cost of your Affliction spells by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4768794, 'EffectSpellClassMaskA_2': 2363163, 'EffectSpellClassMaskB_1': 2169291802, 'EffectSpellClassMaskB_2': 2395931, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


suppression_18175 = spell(
    id=18175,
    name='Suppression',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=199, misc_value=36),
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=150,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your chance to hit with spells by $s1%, and reduces the mana cost of your Affliction spells by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2152252442, 'EffectSpellClassMaskA_2': 266011, 'EffectSpellClassMaskB_1': 2165097498, 'EffectSpellClassMaskB_2': 2395931, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


suppression_18176 = spell(
    id=18176,
    name='Suppression',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=199, misc_value=36),
        Effect(type=EffectType.APPLY_AURA, base_points=-7, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=150,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your chance to hit with spells by $s1%, and reduces the mana cost of your Affliction spells by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2152252442, 'EffectSpellClassMaskA_2': 266011, 'EffectSpellClassMaskB_1': 2169291802, 'EffectSpellClassMaskB_2': 2395931, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_curses_18179 = spell(
    id=18179,
    name='Improved Curses',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=12),
    ],
    spell_icon_id=543,
    notes='warlock-rework AFFLICTION §6 (1,2): renamed from Improved Curse of Weakness and widened to cover Curse of Exhaustion/Tongues/the Elements; eff1 op changed EFFECT1(3)->ALL_EFFECTS(8) so it scopes both of Curse of Weakness effects; eff2 (new) ALL_EFFECTS on Exhaustion+Tongues; eff3 (new) flat EFFECT2 bump on Curse of the Elements eff2. §11 Q6/table also grants Agony stack cap (+2/+5), read live by Warlock::GetAgonyStackCap - no data field for that clause.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the maximum stack count of your Bane of Agony by 2.  Increases the effect of your Curse of Weakness by $s1%, the effect of your Curse of Exhaustion and Curse of Tongues by $s2%, and the damage taken increase of your Curse of the Elements by $s3 percentage points.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.CURSE_OF_WEAKNESS, 'EffectSpellClassMaskB_1': m.IMPROVED_CURSES_EXH_TONGUES[0], 'EffectSpellClassMaskB_3': m.IMPROVED_CURSES_EXH_TONGUES[2], 'EffectSpellClassMaskC_2': m.CURSE_OF_THE_ELEMENTS, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_curses_18180 = spell(
    id=18180,
    name='Improved Curses',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=12),
    ],
    spell_icon_id=543,
    notes='warlock-rework AFFLICTION §6 (1,2)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the maximum stack count of your Bane of Agony by 5.  Increases the effect of your Curse of Weakness by $s1%, the effect of your Curse of Exhaustion and Curse of Tongues by $s2%, and the damage taken increase of your Curse of the Elements by $s3 percentage points.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.CURSE_OF_WEAKNESS, 'EffectSpellClassMaskB_1': m.IMPROVED_CURSES_EXH_TONGUES[0], 'EffectSpellClassMaskB_3': m.IMPROVED_CURSES_EXH_TONGUES[2], 'EffectSpellClassMaskC_2': m.CURSE_OF_THE_ELEMENTS, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_life_tap_18182 = spell(
    id=18182,
    name='Improved Life Tap',
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
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=208,
    notes='warlock-rework AFFLICTION §6 (1,1): bp raised 9->19 (10%->20%, PLAN §1 rank-count target 20/40/60%). C++ (spell_warl_life_tap_affliction) reads this by rank id.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the mana gained from your Life Tap by $s1%.  Your Life Tap restores 50% more mana when used below 50% mana.\n\n|cFF9D9D9DCapstone Bonus: Using Life Tap increases your spell power by 10% for 15 sec.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_life_tap_18183 = spell(
    id=18183,
    name='Improved Life Tap',
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
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=208,
    notes='warlock-rework AFFLICTION §6 (1,1): bp raised 19->39 (20%->40%).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the mana gained from your Life Tap by $s1%.  Your Life Tap restores 50% more mana when used below 50% mana.\n\n|cFF9D9D9DCapstone Bonus: Using Life Tap increases your spell power by 10% for 15 sec.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_life_tap_200765 = spell(
    id=200765,
    name='Improved Life Tap',
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
        Effect(type=EffectType.APPLY_AURA, base_points=59, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=208,
    notes='warlock-rework AFFLICTION §6 (1,1): new rank 3 (talent 1007 rank count 2->3, PLAN §1); capstone: casting Life Tap grants Improved Life Tap self buff 200726 (10% SP, 15s) - data only, C++ in spell_warl_life_tap_affliction.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the mana gained from your Life Tap by $s1%.  Your Life Tap restores 50% more mana when used below 50% mana.\n\nCapstone Bonus: Using Life Tap increases your spell power by 10% for 15 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


siphon_power_18213 = spell(
    id=18213,
    name='Siphon Power',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=18),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=108, misc_value=2),
        Effect(type=EffectType.DUMMY, base_points=11, implicit_target_a=1),
    ],
    spell_icon_id=113,
    notes='warlock-rework AFFLICTION §6 (1,3): renamed from Improved Drain Soul (kept); eff1 unchanged; eff2 mask widened to AFFLICTION_THREAT; eff3 bp raised 6->11 (12%, read by the stock -18213 KILL proc class, spell_warlock.cpp:1499).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Returns $s3% of your maximum mana if the target is killed by you while you drain its soul.  When a target dies while you are draining its soul, you gain 10% increased spell power for 15 sec.  Your Affliction spells generate $s2% less threat.\n\n|cFF9D9D9DCapstone Bonus: Inevitable Demise. Each time your Bane of Agony deals damage, the damage of your next Drain Life is increased by 5%, stacking up to 50 times.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 16384, 'EffectSpellClassMaskB_1': m.AFFLICTION_THREAT[0], 'EffectSpellClassMaskB_2': m.AFFLICTION_THREAT[1], 'EffectSpellClassMaskB_3': m.AFFLICTION_THREAT[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


grim_reach_18218 = spell(
    id=18218,
    name='Grim Reach',
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
    ],
    spell_icon_id=1614,
    notes='warlock-rework AFFLICTION §6 (3,1) / A3: range SpellMod removed from this rank (a range aura 107 cannot be spell_group-gated) - eff1 is now an inert DUMMY marker, the real +3 yd effect lives on the hidden shared passive 200707, joined via linked_spell below (type=2).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of your damaging spells by $s1 yards.\n\n|cFF9D9D9DCapstone Bonus: Your periodic Shadow damage has a 5% chance to deal additional Shadow damage and increase the Shadow damage the target takes from you by 3% for 6 sec.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
linked_spell(grim_reach_18218.id, 200707, type=2)


grim_reach_18219 = spell(
    id=18219,
    name='Grim Reach',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1614,
    notes='warlock-rework AFFLICTION §6 (3,1) capstone: rank 2 links to the shared +6 yd passive 200708 and carries the "periodic Shadow damage has a 5% chance to bolt+debuff" capstone proc (spell_warl_grim_reach_capstone, procs_on below).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of your damaging spells by $s1 yards.\n\nCapstone Bonus: Your periodic Shadow damage has a 5% chance to deal additional Shadow damage and increase the Shadow damage the target takes from you by 3% for 6 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
linked_spell(grim_reach_18219.id, 200708, type=2)
scripted_by(grim_reach_18219, 'spell_warl_grim_reach_capstone')
procs_on(grim_reach_18219, proc_flags=m.PROC_FLAG_DONE_PERIODIC, school_mask=32, spell_type_mask=1, spell_phase_mask=m.PROC_SPELL_PHASE_HIT, chance=5, cooldown_ms=0)


shadow_mastery_18271 = spell(
    id=18271,
    name='Shadow Mastery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=22,
    notes='warlock-rework AFFLICTION §6 (5,1): eff1 bp 2->1 (2%), masks -> SHADOW_MASTERY_DIRECT (keeps the detonation bit 0x10, adds PS/TS/GR/AP bolts); eff2 bp 2->1, mask -> SHADOW_MASTERY_DOT (adds Curse of Doom, Seed DoT rebit, UA).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage dealt or life drained by your Shadow spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.SHADOW_MASTERY_DIRECT[0], 'EffectSpellClassMaskA_2': m.SHADOW_MASTERY_DIRECT[1], 'EffectSpellClassMaskA_3': m.SHADOW_MASTERY_DIRECT[2], 'EffectSpellClassMaskB_1': m.SHADOW_MASTERY_DOT[0], 'EffectSpellClassMaskB_2': m.SHADOW_MASTERY_DOT[1], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


shadow_mastery_18272 = spell(
    id=18272,
    name='Shadow Mastery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=22,
    notes='warlock-rework AFFLICTION §6 (5,1): bp 5->3 (4%).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage dealt or life drained by your Shadow spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.SHADOW_MASTERY_DIRECT[0], 'EffectSpellClassMaskA_2': m.SHADOW_MASTERY_DIRECT[1], 'EffectSpellClassMaskA_3': m.SHADOW_MASTERY_DIRECT[2], 'EffectSpellClassMaskB_1': m.SHADOW_MASTERY_DOT[0], 'EffectSpellClassMaskB_2': m.SHADOW_MASTERY_DOT[1], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


shadow_mastery_18273 = spell(
    id=18273,
    name='Shadow Mastery',
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
    ],
    spell_icon_id=22,
    notes='warlock-rework AFFLICTION §6 (5,1): bp 8->5 (6%).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage dealt or life drained by your Shadow spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.SHADOW_MASTERY_DIRECT[0], 'EffectSpellClassMaskA_2': m.SHADOW_MASTERY_DIRECT[1], 'EffectSpellClassMaskA_3': m.SHADOW_MASTERY_DIRECT[2], 'EffectSpellClassMaskB_1': m.SHADOW_MASTERY_DOT[0], 'EffectSpellClassMaskB_2': m.SHADOW_MASTERY_DOT[1], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


shadow_mastery_18274 = spell(
    id=18274,
    name='Shadow Mastery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=22,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage dealt or life drained by your Shadow spells and your Felhunter's Shadow Bite ability by $s1%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 524433, 'EffectSpellClassMaskA_2': 4528400, 'EffectSpellClassMaskB_1': 17418, 'EffectSpellClassMaskB_2': 275, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


shadow_mastery_18275 = spell(
    id=18275,
    name='Shadow Mastery',
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
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=22,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage dealt or life drained by your Shadow spells and your Felhunter's Shadow Bite ability by $s1%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 524433, 'EffectSpellClassMaskA_2': 4528400, 'EffectSpellClassMaskB_1': 17418, 'EffectSpellClassMaskB_2': 275, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


amplify_curse_18288 = spell(
    id=18288,
    name='Amplify Curse',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    attributes=65984,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=-501, implicit_target_a=1, apply_aura=107, misc_value=21),
    ],
    spell_icon_id=1494,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Reduces the global cooldown of your Curses by ${$m2/-1000}.1 sec.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the global cooldown of your Curses by ${$m2/-1000}.1 sec.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1024, 'EffectSpellClassMaskA_2': 2, 'EffectSpellClassMaskB_1': 4228096, 'EffectSpellClassMaskB_2': 2097666, 'EffectSpellClassMaskB_3': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5, 'SpellVisualID_1': 4600},
)


siphon_power_18372 = spell(
    id=18372,
    name='Siphon Power',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=18),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=108, misc_value=2),
        Effect(type=EffectType.DUMMY, base_points=24, implicit_target_a=1),
    ],
    spell_icon_id=113,
    notes='warlock-rework AFFLICTION §6 (1,3) capstone: eff3 bp raised 14->24 (25%); linked_spell to the Inevitable Demise capstone passive 200769 below.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Returns $s3% of your maximum mana if the target is killed by you while you drain its soul.  When a target dies while you are draining its soul, you gain 10% increased spell power for 15 sec.  Your Affliction spells generate $s2% less threat.\n\nCapstone Bonus: Inevitable Demise. Each time your Bane of Agony deals damage, the damage of your next Drain Life is increased by 5%, stacking up to 50 times.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 16384, 'EffectSpellClassMaskB_1': m.AFFLICTION_THREAT[0], 'EffectSpellClassMaskB_2': m.AFFLICTION_THREAT[1], 'EffectSpellClassMaskB_3': m.AFFLICTION_THREAT[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
linked_spell(siphon_power_18372.id, 200769, type=2)
procs_on(-18213, proc_flags=m.PROC_FLAG_KILL, school_mask=32, family_name=5, family_mask=(0x4000, 0, 0), attributes_mask=m.PROC_ATTR_REQ_EXP_OR_HONOR, chance=0, cooldown_ms=0)


improved_healthstone_18692 = spell(
    id=18692,
    name='Improved Healthstone',
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
    ],
    spell_icon_id=284,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount of Health restored by your Healthstone by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_healthstone_18693 = spell(
    id=18693,
    name='Improved Healthstone',
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
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=284,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount of Health restored by your Healthstone by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_imp_18694 = spell(
    id=18694,
    name='Improved Imp',
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
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=215,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the effect of your Imp's Firebolt, Fire Shield, and Blood Pact spells by $s1%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 8392704, 'EffectSpellClassMaskA_1': 8392704, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_imp_18695 = spell(
    id=18695,
    name='Improved Imp',
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
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=215,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the effect of your Imp's Firebolt, Fire Shield, and Blood Pact spells by $s1%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 8392704, 'EffectSpellClassMaskA_1': 8392704, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_imp_18696 = spell(
    id=18696,
    name='Improved Imp',
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
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=215,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the effect of your Imp's Firebolt, Fire Shield, and Blood Pact spells by $s1%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 8392704, 'EffectSpellClassMaskA_1': 8392704, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_health_funnel_18703 = spell(
    id=18703,
    name='Improved Health Funnel',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=153,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount of Health transferred by your Health Funnel spell by $s1% and reduces the health cost by $s2%. In addition, your summoned Demon takes $60955s1% less damage while under the effect of your Health Funnel.', 'EffectBasePoints_3': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 16777216, 'EffectSpellClassMaskB_1': 16777216, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_health_funnel_18704 = spell(
    id=18704,
    name='Improved Health Funnel',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=153,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount of Health transferred by your Health Funnel spell by $s1% and reduces the health cost by $s2%. In addition, your summoned Demon takes $60956s1% less damage while under the effect of your Health Funnel.', 'EffectBasePoints_3': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 16777216, 'EffectSpellClassMaskB_1': 16777216, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


demonic_brutality_18705 = spell(
    id=18705,
    name='Demonic Brutality',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=107, misc_value=3),
    ],
    spell_icon_id=217,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the effectiveness of your Voidwalker's Torment, Consume Shadows, Sacrifice and Suffering spells by $s1%, and increases the attack power bonus on your Felguard's Demonic Frenzy effect by $s2%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 33554432, 'EffectSpellClassMaskB_3': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


demonic_brutality_18706 = spell(
    id=18706,
    name='Demonic Brutality',
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
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=3),
    ],
    spell_icon_id=217,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the effectiveness of your Voidwalker's Torment, Consume Shadows, Sacrifice and Suffering spells by $s1%, and increases the attack power bonus on your Felguard's Demonic Frenzy effect by $s2%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 33554432, 'EffectSpellClassMaskB_3': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


demonic_brutality_18707 = spell(
    id=18707,
    name='Demonic Brutality',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=107, misc_value=3),
    ],
    spell_icon_id=217,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the effectiveness of your Voidwalker's Torment, Consume Shadows, Sacrifice and Suffering spells by $s1%, and increases the attack power bonus on your Felguard's Demonic Frenzy effect by $s2%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 33554432, 'EffectSpellClassMaskB_3': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


master_summoner_18709 = spell(
    id=18709,
    name='Master Summoner',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-2001, implicit_target_a=1, apply_aura=107, misc_value=10),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=211,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the casting time of your Imp, Voidwalker, Succubus, Felhunter and Fel Guard Summoning spells by $/1000;s1 sec and the Mana cost by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectItemType_1': 536870912, 'EffectItemType_2': 536870912, 'EffectSpellClassMaskA_1': 536870912, 'EffectSpellClassMaskB_1': 536870912, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


master_summoner_18710 = spell(
    id=18710,
    name='Master Summoner',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-4001, implicit_target_a=1, apply_aura=107, misc_value=10),
        Effect(type=EffectType.APPLY_AURA, base_points=-41, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=211,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the casting time of your Imp, Voidwalker, Succubus, Felhunter and Fel Guard Summoning spells by $/1000;s1 sec and the Mana cost by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectItemType_1': 536870912, 'EffectItemType_2': 536870912, 'EffectSpellClassMaskA_1': 536870912, 'EffectSpellClassMaskB_1': 536870912, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


fel_vitality_18731 = spell(
    id=18731,
    name='Fel Vitality',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=107, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=132),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=133),
    ],
    spell_icon_id=125,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the Stamina and Intellect of your Imp, Voidwalker, Succubus, Felhunter and Felguard by $s1% and increases your maximum health and mana by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 402653184, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


fel_vitality_18743 = spell(
    id=18743,
    name='Fel Vitality',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=132),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=133),
    ],
    spell_icon_id=125,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the Stamina and Intellect of your Imp, Voidwalker, Succubus, Felhunter and Felguard by $s1% and increases your maximum health and mana by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 402653184, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


fel_vitality_18744 = spell(
    id=18744,
    name='Fel Vitality',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=107, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=132),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=133),
    ],
    spell_icon_id=125,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the Stamina and Intellect of your Imp, Voidwalker, Succubus, Felhunter and Felguard by $s1% and increases your maximum health and mana by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 402653184, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_succubus_18754 = spell(
    id=18754,
    name='Improved Succubus',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-23, implicit_target_a=5, apply_aura=108, misc_value=10),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=1),
    ],
    spell_icon_id=216,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces the cast time of your Succubus' Seduction by $s1%, and increases the duration of your Succubus' Seduction and Lesser Invisibility spells by $s2%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1073741824, 'EffectSpellClassMaskB_1': 1073741824, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_succubus_18755 = spell(
    id=18755,
    name='Improved Succubus',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-45, implicit_target_a=5, apply_aura=108, misc_value=10),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=1),
    ],
    spell_icon_id=216,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces the cast time of your Succubus' Seduction by $s1%, and increases the duration of your Succubus' Seduction and Lesser Invisibility spells by $s2%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1073741824, 'EffectSpellClassMaskB_1': 1073741824, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_succubus_18756 = spell(
    id=18756,
    name='Improved Succubus',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-67, implicit_target_a=5, apply_aura=108, misc_value=10),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108, misc_value=1),
    ],
    spell_icon_id=216,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces the cast time of your Succubus' Seduction by $s1%, and increases the duration of your Succubus' Seduction and Lesser Invisibility spells by $s2%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1073741824, 'EffectSpellClassMaskB_1': 1073741824, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


master_conjuror_18767 = spell(
    id=18767,
    name='Master Conjuror',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=149, implicit_target_a=1, apply_aura=108, misc_value=23),
        Effect(type=EffectType.APPLY_AURA, base_points=149, implicit_target_a=1, apply_aura=108, misc_value=23),
    ],
    spell_icon_id=1506,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the combat ratings gained from your conjured Firestone and Spellstone by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2097152, 'EffectSpellClassMaskB_1': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


master_conjuror_18768 = spell(
    id=18768,
    name='Master Conjuror',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=299, implicit_target_a=1, apply_aura=108, misc_value=23),
        Effect(type=EffectType.APPLY_AURA, base_points=299, implicit_target_a=1, apply_aura=108, misc_value=23),
    ],
    spell_icon_id=1506,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the combat ratings gained from your conjured Firestone and Spellstone by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2097152, 'EffectSpellClassMaskB_1': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


unholy_power_18769 = spell(
    id=18769,
    name='Unholy Power',
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
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=107, misc_value=8),
    ],
    spell_icon_id=235,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage done by your Voidwalker, Succubus, Felhunter and Felguard's melee attacks and your Imp's Firebolt by $s1%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectItemType_1': 67108864, 'EffectSpellClassMaskA_1': 67108864, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


unholy_power_18770 = spell(
    id=18770,
    name='Unholy Power',
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
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=107, misc_value=8),
    ],
    spell_icon_id=235,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage done by your Voidwalker, Succubus, Felhunter and Felguard's melee attacks and your Imp's Firebolt by $s1%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectItemType_1': 67108864, 'EffectSpellClassMaskA_1': 67108864, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


unholy_power_18771 = spell(
    id=18771,
    name='Unholy Power',
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
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=107, misc_value=8),
    ],
    spell_icon_id=235,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage done by your Voidwalker, Succubus, Felhunter and Felguard's melee attacks and your Imp's Firebolt by $s1%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectItemType_1': 67108864, 'EffectSpellClassMaskA_1': 67108864, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


unholy_power_18772 = spell(
    id=18772,
    name='Unholy Power',
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
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=107, misc_value=8),
    ],
    spell_icon_id=235,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage done by your Voidwalker, Succubus, Felhunter and Felguard's melee attacks and your Imp's Firebolt by $s1%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectItemType_1': 67108864, 'EffectSpellClassMaskA_1': 67108864, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


unholy_power_18773 = spell(
    id=18773,
    name='Unholy Power',
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
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=107, misc_value=8),
    ],
    spell_icon_id=235,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage done by your Voidwalker, Succubus, Felhunter and Felguard's melee attacks and your Imp's Firebolt by $s1%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectItemType_1': 67108864, 'EffectSpellClassMaskA_1': 67108864, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_bane_of_agony_18827 = spell(
    id=18827,
    name='Improved Bane of Agony',
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
    spell_icon_id=544,
    notes='warlock-rework AFFLICTION §6 (0,2): renamed from Improved Curse of Agony; bp raised 4->9 (10%). Capstone (r2): Bane of Agonys damage is increased by Mastery - script only (spell_warl_bane_of_agony DoEffectCalcAmount, HasAura(18829)).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage done by your Bane of Agony by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Your Bane of Agony's damage is increased by your Mastery.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_bane_of_agony_18829 = spell(
    id=18829,
    name='Improved Bane of Agony',
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
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=544,
    notes='warlock-rework AFFLICTION §6 (0,2): bp raised 9->19 (20%).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage done by your Bane of Agony by $s1%.\n\nCapstone Bonus: Your Bane of Agony's damage is increased by your Mastery.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_howl_of_terror_30054 = spell(
    id=30054,
    name='Improved Howl of Terror',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-801, implicit_target_a=1, apply_aura=107, misc_value=10),
    ],
    spell_icon_id=134,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the casting time of your Howl of Terror spell by $/1000;S1 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_howl_of_terror_30057 = spell(
    id=30057,
    name='Improved Howl of Terror',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-1501, implicit_target_a=1, apply_aura=107, misc_value=10),
    ],
    spell_icon_id=134,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the casting time of your Howl of Terror spell by $/1000;S1 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


contagion_30060 = spell(
    id=30060,
    name='Contagion',
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
    ],
    spell_icon_id=1978,
    notes='warlock-rework AFFLICTION §6 (6,0): rewritten from three SpellMod effects into a single DUMMY marker read by spell_warl_corruption_affliction (the empowered-6th-tick %, and the capstone spread condition at r3); no classmask needed.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Every 6th tick of your Corruption deals $s1% increased damage.\n\n|cFF9D9D9DCapstone Bonus: If a 6th tick occurs while you are draining the target's soul, the area becomes contaminated, spreading Corruption to all targets within 10 yards.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


contagion_30061 = spell(
    id=30061,
    name='Contagion',
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
    ],
    spell_icon_id=1978,
    notes='warlock-rework AFFLICTION §6 (6,0)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Every 6th tick of your Corruption deals $s1% increased damage.\n\n|cFF9D9D9DCapstone Bonus: If a 6th tick occurs while you are draining the target's soul, the area becomes contaminated, spreading Corruption to all targets within 10 yards.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


contagion_30062 = spell(
    id=30062,
    name='Contagion',
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
    ],
    spell_icon_id=1978,
    notes='warlock-rework AFFLICTION §6 (6,0) capstone: rank 3 carries the "6th tick while draining Drain Soul spreads Corruption" clause (spell_warl_corruption_affliction) - data only, C++ is WP-B.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Every 6th tick of your Corruption deals $s1% increased damage.\n\nCapstone Bonus: If a 6th tick occurs while you are draining the target's soul, the area becomes contaminated, spreading Corruption to all targets within 10 yards.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


contagion_30063 = spell(
    id=30063,
    name='Contagion',
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
        Effect(type=EffectType.APPLY_AURA, base_points=23, implicit_target_a=1, apply_aura=107, misc_value=28),
    ],
    spell_icon_id=1978,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of Curse of Agony, Corruption and Seed of Corruption by $s1% and reduces the chance your helpful Affliction spells and damage over time effects  will be dispelled by an additional $s3%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1026, 'EffectSpellClassMaskA_2': 16, 'EffectSpellClassMaskB_2': 16, 'EffectSpellClassMaskC_1': 17418, 'EffectSpellClassMaskC_2': 275, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


contagion_30064 = spell(
    id=30064,
    name='Contagion',
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
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=107, misc_value=28),
    ],
    spell_icon_id=1978,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of Curse of Agony, Corruption and Seed of Corruption by $s1% and reduces the chance your helpful Affliction spells and damage over time effects  will be dispelled by an additional $s3%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1026, 'EffectSpellClassMaskA_2': 16, 'EffectSpellClassMaskB_2': 16, 'EffectSpellClassMaskC_1': 17418, 'EffectSpellClassMaskC_2': 275, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


demonic_aegis_30143 = spell(
    id=30143,
    name='Demonic Aegis',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=89,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effectiveness of your Demon Armor and Fel Armor spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 536870944, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


demonic_aegis_30144 = spell(
    id=30144,
    name='Demonic Aegis',
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
    ],
    spell_icon_id=89,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effectiveness of your Demon Armor and Fel Armor spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 536870944, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


demonic_aegis_30145 = spell(
    id=30145,
    name='Demonic Aegis',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=89,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effectiveness of your Demon Armor and Fel Armor spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 536870944, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


demonic_tactics_30242 = spell(
    id=30242,
    name='Demonic Tactics',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=57),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=52),
    ],
    spell_icon_id=1981,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases melee and spell critical strike chance for you and your summoned demon by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


demonic_tactics_30245 = spell(
    id=30245,
    name='Demonic Tactics',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=107, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=57),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=52),
    ],
    spell_icon_id=1981,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases melee and spell critical strike chance for you and your summoned demon by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


demonic_tactics_30246 = spell(
    id=30246,
    name='Demonic Tactics',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=107, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=57),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=52),
    ],
    spell_icon_id=1981,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases melee and spell critical strike chance for you and your summoned demon by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


demonic_tactics_30247 = spell(
    id=30247,
    name='Demonic Tactics',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=107, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=57),
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=52),
    ],
    spell_icon_id=1981,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases melee and spell critical strike chance for you and your summoned demon by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


demonic_tactics_30248 = spell(
    id=30248,
    name='Demonic Tactics',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=57),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=52),
    ],
    spell_icon_id=1981,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases melee and spell critical strike chance for you and your summoned demon by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


shadow_and_flame_30288 = spell(
    id=30288,
    name='Shadow and Flame',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-2001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=1986,
    notes='warlock-rework DESTRUCTION §6 (7,1): eff0 bp 3/7/11 -> 6/13/19 (7/14/20%), mask -> SHADOW_AND_FLAME_SPELLS (Hand of Guldan removed). New eff1 ADD_FLAT_MODIFIER COOLDOWN bp -2001/-4001/-6001 (-2/-4/-6s), B_2 = SHADOWFLAME (0x10000, its own 15s category CD).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the spell damage scaling of your Shadow Bolt, Shadowburn, Chaos Bolt, Shadowfury, Soul Fire, Incinerate and Shadowflame by $s1%. Reduces the cooldown of Shadowflame by $/-1000;s2 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.SHADOW_AND_FLAME_SPELLS[0], 'EffectSpellClassMaskA_2': m.SHADOW_AND_FLAME_SPELLS[1], 'EffectSpellClassMaskA_3': m.SHADOW_AND_FLAME_SPELLS[2], 'EffectSpellClassMaskB_2': m.SHADOWFLAME, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


shadow_and_flame_30289 = spell(
    id=30289,
    name='Shadow and Flame',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-4001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=1986,
    notes='warlock-rework DESTRUCTION §6 (7,1): see rank 1s note.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the spell damage scaling of your Shadow Bolt, Shadowburn, Chaos Bolt, Shadowfury, Soul Fire, Incinerate and Shadowflame by $s1%. Reduces the cooldown of Shadowflame by $/-1000;s2 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.SHADOW_AND_FLAME_SPELLS[0], 'EffectSpellClassMaskA_2': m.SHADOW_AND_FLAME_SPELLS[1], 'EffectSpellClassMaskA_3': m.SHADOW_AND_FLAME_SPELLS[2], 'EffectSpellClassMaskB_2': m.SHADOWFLAME, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


shadow_and_flame_30290 = spell(
    id=30290,
    name='Shadow and Flame',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-6001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=1986,
    notes='warlock-rework DESTRUCTION §6 (7,1): r3 final rank, see rank 1s note.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the spell damage scaling of your Shadow Bolt, Shadowburn, Chaos Bolt, Shadowfury, Soul Fire, Incinerate and Shadowflame by $s1%. Reduces the cooldown of Shadowflame by $/-1000;s2 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.SHADOW_AND_FLAME_SPELLS[0], 'EffectSpellClassMaskA_2': m.SHADOW_AND_FLAME_SPELLS[1], 'EffectSpellClassMaskA_3': m.SHADOW_AND_FLAME_SPELLS[2], 'EffectSpellClassMaskB_2': m.SHADOWFLAME, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


shadow_and_flame_30291 = spell(
    id=30291,
    name='Shadow and Flame',
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
    spell_icon_id=1986,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Shadow Bolt, Shadowburn, Chaos Bolt and Incinerate spells gain an additional $s1% of your bonus spell damage effects.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 129, 'EffectSpellClassMaskA_2': 131136, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


shadow_and_flame_30292 = spell(
    id=30292,
    name='Shadow and Flame',
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
    spell_icon_id=1986,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Shadow Bolt, Shadowburn, Chaos Bolt and Incinerate spells gain an additional $s1% of your bonus spell damage effects.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 129, 'EffectSpellClassMaskA_2': 131136, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


soul_leech_30293 = spell(
    id=30293,
    name='Soul Leech',
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
    ],
    spell_icon_id=2027,
    notes='warlock-rework DESTRUCTION §6 (6,2): eff0 bp 19 -> 4 (5%), junk masks cleared. ProcChance 10 -> 100, ProcTypeMask -> DONE_SPELL_MAGIC_DMG_CLASS_NEG (0x10000). Only one leech talent works (SHARED §4, §0.2 item 9, §7.11) - unbind_script(-30293) below, spell_warl_soul_leech_destruction (WP-B) checks Warlock::GetActiveLeechTalent.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your direct single target Destruction spells heal you for $s1% of the damage caused. Each heal returns at most 15% of your health. This effect can only occur once every 3 seconds. Does not stack with other similar effects.\n\n|cFF9D9D9DCapstone Bonus: Your Soul Leech also restores mana to you and your summoned demon equal to 4% of your missing mana, and grants Replenishment.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 0, 'EffectSpellClassMaskA_2': 0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 5},
)
unbind_script(-30293, 'spell_warl_soul_leech')
scripted_by(30293, 'spell_warl_soul_leech_destruction')


soul_leech_30295 = spell(
    id=30295,
    name='Soul Leech',
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
    ],
    spell_icon_id=2027,
    notes='warlock-rework DESTRUCTION §6 (6,2): see rank 1s note.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your direct single target Destruction spells heal you for $s1% of the damage caused. Each heal returns at most 15% of your health. This effect can only occur once every 3 seconds. Does not stack with other similar effects.\n\n|cFF9D9D9DCapstone Bonus: Your Soul Leech also restores mana to you and your summoned demon equal to 4% of your missing mana, and grants Replenishment.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 0, 'EffectSpellClassMaskA_2': 0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 5},
)
scripted_by(30295, 'spell_warl_soul_leech_destruction')


soul_leech_30296 = spell(
    id=30296,
    name='Soul Leech',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2027,
    notes='warlock-rework DESTRUCTION §6 (6,2): r3 final rank, eff0 bp 14 (15%); capstone (mana/Replenishment to warlock+demon) implemented in spell_warl_soul_leech_destruction (§7.11), no new effect slot needed (r3 already at 3 effects would need one, but the capstone reads r3 by talent rank and grants the mana/Replenishment as a script side effect off the same DUMMY proc).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your direct single target Destruction spells heal you for $s1% of the damage caused. Each heal returns at most 15% of your health. This effect can only occur once every 3 seconds. Does not stack with other similar effects.\n\nCapstone Bonus: Your Soul Leech also restores mana to you and your summoned demon equal to 4% of your missing mana, and grants Replenishment.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 0, 'EffectSpellClassMaskA_2': 0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 5},
)
scripted_by(30296, 'spell_warl_soul_leech_destruction')
procs_on(-30293, proc_flags=m.PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG, family_name=5, family_mask=m.SOUL_LEECH_SPELLS, spell_type_mask=m.PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=m.PROC_SPELL_PHASE_HIT, chance=100, cooldown_ms=3000)


nether_protection_30299 = spell(
    id=30299,
    name='Nether Protection',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=1206),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1985,
    notes='warlock-rework DESTRUCTION §6 (5,0): eff0 kept (stock spell_warl_nether_protection, -30299, still bound); ProcChance 10/20/30 -> 0/0/20 (r3 only), ProcTypeMask -> 0xA0000 (HIT + TAKEN_PERIODIC, §8). New eff1 DUMMY bp 1/3/5 (2/4/6%) - the periodic-taken reduction itself is data-only via warlock_hooks.cpp ModifyPeriodicDamageAurasTick (WP-B, §7.12), reading whichever rank is present.',
    raw_overrides={'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces periodic spell damage taken by $s2%.\n\n|cFF9D9D9DCapstone Bonus: When you are hit by a spell or take periodic spell damage, you have a 20% chance to gain Nether Protection, reducing damage taken from that spell\'s school by 10% for 6 sec. Cannot occur more than once every 4 sec.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 997, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 0, 'ProcTypeMask': 655360, 'RangeIndex': 1, 'SpellClassSet': 5},
)


nether_protection_30301 = spell(
    id=30301,
    name='Nether Protection',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=1206),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1985,
    notes='warlock-rework DESTRUCTION §6 (5,0): see rank 1s note.',
    raw_overrides={'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces periodic spell damage taken by $s2%.\n\n|cFF9D9D9DCapstone Bonus: When you are hit by a spell or take periodic spell damage, you have a 20% chance to gain Nether Protection, reducing damage taken from that spell\'s school by 10% for 6 sec. Cannot occur more than once every 4 sec.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 997, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 0, 'ProcTypeMask': 655360, 'RangeIndex': 1, 'SpellClassSet': 5},
)


nether_protection_30302 = spell(
    id=30302,
    name='Nether Protection',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=1206),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1985,
    notes='warlock-rework DESTRUCTION §6 (5,0): r3 final rank, keeps the DBC proc (chance 20) for the school-buff capstone (stock spell_warl_nether_protection, -30299, casts 54370-75). Nether Protection capstone excludes self-inflicted damage (§11 Q23) via an additive DoCheckProc class (WP-B).',
    raw_overrides={'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces periodic spell damage taken by $s2%.\n\nCapstone Bonus: When you are hit by a spell or take periodic spell damage, you have a 20% chance to gain Nether Protection, reducing damage taken from that spell\'s school by 10% for 6 sec. Cannot occur more than once every 4 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 997, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'ProcTypeMask': 655360, 'RangeIndex': 1, 'SpellClassSet': 5},
)
scripted_by(nether_protection_30302, 'spell_warl_nether_protection_destruction')
procs_on(-30299, proc_flags=m.PROC_FLAG_TAKEN_SPELL_MAGIC_DMG_CLASS_NEG | m.PROC_FLAG_TAKEN_PERIODIC, school_mask=126, spell_phase_mask=m.PROC_SPELL_PHASE_HIT, chance=0, cooldown_ms=4000)


demonic_resilience_30319 = spell(
    id=30319,
    name='Demonic Resilience',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-2, implicit_target_a=1, apply_aura=187),
        Effect(type=EffectType.APPLY_AURA, base_points=-6, implicit_target_a=1, apply_aura=107, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=-2, implicit_target_a=1, apply_aura=179, misc_value=126),
    ],
    spell_icon_id=1980,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces the chance you'll be critically hit by melee and spells by $s1% and reduces all damage your summoned demon takes by $s2%.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 67108864, 'EffectSpellClassMaskB_2': 16384, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


demonic_resilience_30320 = spell(
    id=30320,
    name='Demonic Resilience',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=187),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=107, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=179, misc_value=126),
    ],
    spell_icon_id=1980,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces the chance you'll be critically hit by melee and spells by $s1% and reduces all damage your summoned demon takes by $s2%.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 67108864, 'EffectSpellClassMaskB_2': 16384, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


demonic_resilience_30321 = spell(
    id=30321,
    name='Demonic Resilience',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-4, implicit_target_a=1, apply_aura=187),
        Effect(type=EffectType.APPLY_AURA, base_points=-16, implicit_target_a=1, apply_aura=107, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=-4, implicit_target_a=1, apply_aura=179, misc_value=126),
    ],
    spell_icon_id=1980,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces the chance you'll be critically hit by melee and spells by $s1% and reduces all damage your summoned demon takes by $s2%.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 67108864, 'EffectSpellClassMaskB_2': 16384, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


mana_feed_30326 = spell(
    id=30326,
    name='Mana Feed',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=107, misc_value=12),
    ],
    spell_icon_id=1982,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you gain mana from Drain Mana or Life Tap spells, your summoned demon gains $s1% of the mana you gain.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


empowered_corruption_32381 = spell(
    id=32381,
    name='Empowered Corruption',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=24),
    ],
    spell_icon_id=97,
    notes='warlock-rework AFFLICTION §6 (3,0): op changed ADD_FLAT_MODIFIER(107)->ADD_PCT_MODIFIER(108) BONUS_MULTIPLIER (10/20/30% of the coefficient, not a flat SP fraction); icon 313 (Improved Corruptions, a stock duplicate) -> 97 so the two talents dont share an icon (tooltip audit).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the spell damage scaling of your Corruption by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


empowered_corruption_32382 = spell(
    id=32382,
    name='Empowered Corruption',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=24),
    ],
    spell_icon_id=97,
    notes='warlock-rework AFFLICTION §6 (3,0)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the spell damage scaling of your Corruption by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


empowered_corruption_32383 = spell(
    id=32383,
    name='Empowered Corruption',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=24),
    ],
    spell_icon_id=97,
    notes='warlock-rework AFFLICTION §6 (3,0)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the spell damage scaling of your Corruption by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


shadow_embrace_32385 = spell(
    id=32385,
    name='Shadow Embrace',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=32386),
    ],
    spell_icon_id=2209,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your direct damage Shadow spells, Drain Life and Drain Soul apply Shadow Embrace, increasing all periodic Shadow damage you deal to the target by $32386s1% per stack.  Lasts $32386d.  Stacks up to $32386u times.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 1026, 'EffectSpellClassMaskB_2': 17, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 5},
)


shadow_embrace_32387 = spell(
    id=32387,
    name='Shadow Embrace',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=32388),
    ],
    spell_icon_id=2209,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your direct damage Shadow spells, Drain Life and Drain Soul apply Shadow Embrace, increasing all periodic Shadow damage you deal to the target by $32388s1% per stack.  Lasts $32388d.  Stacks up to $32386u times.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 1026, 'EffectSpellClassMaskB_2': 17, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 5},
)


shadow_embrace_32392 = spell(
    id=32392,
    name='Shadow Embrace',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=32389),
    ],
    spell_icon_id=2209,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your direct damage Shadow spells, Drain Life and Drain Soul apply Shadow Embrace, increasing all periodic Shadow damage you deal to the target by $32389s1% per stack.  Lasts $32389d.  Stacks up to $32386u times.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 1026, 'EffectSpellClassMaskB_2': 17, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 5},
)
scripted_by(shadow_embrace_32385, 'spell_warl_shadow_embrace_affliction')
scripted_by(shadow_embrace_32387, 'spell_warl_shadow_embrace_affliction')
scripted_by(shadow_embrace_32392, 'spell_warl_shadow_embrace_affliction')
procs_on(-32385, proc_flags=0x50000, school_mask=32, spell_type_mask=1, spell_phase_mask=m.PROC_SPELL_PHASE_HIT, chance=100, cooldown_ms=0)


shadow_embrace_32393 = spell(
    id=32393,
    name='Shadow Embrace',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=32390),
    ],
    spell_icon_id=2209,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Shadow Bolt and Haunt spells apply the Shadow Embrace effect, increasing all shadow periodic damage dealt to the target by you by $32390s1%, and reduces all periodic healing done to the target by $60467s1%. Lasts for $32390d. Stacks up to $32386u times.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2, 'EffectSpellClassMaskB_1': 1026, 'EffectSpellClassMaskB_2': 17, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 5},
)


shadow_embrace_32394 = spell(
    id=32394,
    name='Shadow Embrace',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=32391),
    ],
    spell_icon_id=2209,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Shadow Bolt and Haunt spells apply the Shadow Embrace effect, increasing all shadow periodic damage dealt to the target by you by $32391s1%, and reduces all periodic healing done to the target by $60468s1%. Lasts for $32391d. Stacks up to $32386u times.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2, 'EffectSpellClassMaskB_1': 1026, 'EffectSpellClassMaskB_2': 17, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 5},
)


malediction_32477 = spell(
    id=32477,
    name='Malediction',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=107, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=79, misc_value=127),
    ],
    spell_icon_id=542,
    notes='warlock-rework AFFLICTION §6 (7,1): eff2 misc 126 (magic damage) -> 127 (all damage, "increases all damage done"); eff1 mask widened to CORRUPTION_UA (d2 0x100 added).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all damage done by $s2%.  Increases the periodic critical strike chance of your Corruption and Unstable Affliction spells by $s1%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.CORRUPTION_UA[0], 'EffectSpellClassMaskA_2': m.CORRUPTION_UA[1], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


malediction_32483 = spell(
    id=32483,
    name='Malediction',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=107, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=79, misc_value=127),
    ],
    spell_icon_id=542,
    notes='warlock-rework AFFLICTION §6 (7,1)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all damage done by $s2%.  Increases the periodic critical strike chance of your Corruption and Unstable Affliction spells by $s1%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.CORRUPTION_UA[0], 'EffectSpellClassMaskA_2': m.CORRUPTION_UA[1], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


malediction_32484 = spell(
    id=32484,
    name='Malediction',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=107, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=79, misc_value=127),
    ],
    spell_icon_id=542,
    notes='warlock-rework AFFLICTION §6 (7,1)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all damage done by $s2%.  Increases the periodic critical strike chance of your Corruption and Unstable Affliction spells by $s1%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.CORRUPTION_UA[0], 'EffectSpellClassMaskA_2': m.CORRUPTION_UA[1], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


demonic_knowledge_35691 = spell(
    id=35691,
    name='Demonic Knowledge',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1876,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your spell damage by an amount equal to $s1% of the total of your active demon's Stamina plus Intellect.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 67108864, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


demonic_knowledge_35692 = spell(
    id=35692,
    name='Demonic Knowledge',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1876,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your spell damage by an amount equal to $s1% of the total of your active demon's Stamina plus Intellect.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 67108864, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


demonic_knowledge_35693 = spell(
    id=35693,
    name='Demonic Knowledge',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1876,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your spell damage by an amount equal to $s1% of the total of your active demon's Stamina plus Intellect.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 67108864, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


eradication_47195 = spell(
    id=47195,
    name='Eradication',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=12, trigger_spell=64371),
    ],
    spell_icon_id=3316,
    notes='warlock-rework AFFLICTION §6 (6,3): every rank now triggers the same 64371 buff (was 64368/64370/64371, a stock quirk where only the buffs +20%/10s differed by name, not value); ProcChance 6->3.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you deal damage with Corruption, you have a $h% chance to increase your spell casting speed by $64371s1% for $64371d.  This effect can only occur every 5 sec.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1026, 'EffectSpellClassMaskA_2': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 3, 'ProcTypeMask': 262144, 'RangeIndex': 1, 'SpellClassSet': 5},
)


eradication_47196 = spell(
    id=47196,
    name='Eradication',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=12, trigger_spell=64371),
    ],
    spell_icon_id=3316,
    notes='warlock-rework AFFLICTION §6 (6,3): ProcChance 6->6 (unchanged at rank 2), trigger 64370->64371.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you deal damage with Corruption, you have a $h% chance to increase your spell casting speed by $64371s1% for $64371d.  This effect can only occur every 5 sec.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1026, 'EffectSpellClassMaskA_2': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 6, 'ProcTypeMask': 262144, 'RangeIndex': 1, 'SpellClassSet': 5},
)


eradication_47197 = spell(
    id=47197,
    name='Eradication',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=12, trigger_spell=64371),
    ],
    spell_icon_id=3316,
    notes='warlock-rework AFFLICTION §6 (6,3): ProcChance 6->9.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you deal damage with Corruption, you have a $h% chance to increase your spell casting speed by $64371s1% for $64371d.  This effect can only occur every 5 sec.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1026, 'EffectSpellClassMaskA_2': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 9, 'ProcTypeMask': 262144, 'RangeIndex': 1, 'SpellClassSet': 5},
)
procs_on(-47195, proc_flags=m.PROC_FLAG_DONE_PERIODIC, family_name=5, family_mask=(0x2, 0, 0), spell_type_mask=1, spell_phase_mask=m.PROC_SPELL_PHASE_HIT, chance=0, cooldown_ms=5000)


death_s_embrace_47198 = spell(
    id=47198,
    name="Death's Embrace",
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=112, misc_value=6927),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=112, misc_value=6928),
    ],
    spell_icon_id=3223,
    notes='warlock-rework AFFLICTION §6 (8,3): eff2 mask widened to WARLOCK_SHADOW_DAMAGE',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount drained by your Drain Life by $s1% while your health is at or below 20% health.  Increases the damage done by your Shadow spells and abilities by $s2% when your target is at or below 35% health.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8, 'EffectSpellClassMaskB_1': m.WARLOCK_SHADOW_DAMAGE[0], 'EffectSpellClassMaskB_2': m.WARLOCK_SHADOW_DAMAGE[1], 'EffectSpellClassMaskB_3': m.WARLOCK_SHADOW_DAMAGE[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


death_s_embrace_47199 = spell(
    id=47199,
    name="Death's Embrace",
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=112, misc_value=6925),
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=112, misc_value=6926),
    ],
    spell_icon_id=3223,
    notes='warlock-rework AFFLICTION §6 (8,3): eff2 mask widened to WARLOCK_SHADOW_DAMAGE',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount drained by your Drain Life by $s1% while your health is at or below 20% health.  Increases the damage done by your Shadow spells and abilities by $s2% when your target is at or below 35% health.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8, 'EffectSpellClassMaskB_1': m.WARLOCK_SHADOW_DAMAGE[0], 'EffectSpellClassMaskB_2': m.WARLOCK_SHADOW_DAMAGE[1], 'EffectSpellClassMaskB_3': m.WARLOCK_SHADOW_DAMAGE[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


death_s_embrace_47200 = spell(
    id=47200,
    name="Death's Embrace",
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=112, misc_value=6916),
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=112, misc_value=6917),
    ],
    spell_icon_id=3223,
    notes='warlock-rework AFFLICTION §6 (8,3): eff2 mask widened to WARLOCK_SHADOW_DAMAGE',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount drained by your Drain Life by $s1% while your health is at or below 20% health.  Increases the damage done by your Shadow spells and abilities by $s2% when your target is at or below 35% health.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8, 'EffectSpellClassMaskB_1': m.WARLOCK_SHADOW_DAMAGE[0], 'EffectSpellClassMaskB_2': m.WARLOCK_SHADOW_DAMAGE[1], 'EffectSpellClassMaskB_3': m.WARLOCK_SHADOW_DAMAGE[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


everlasting_affliction_47201 = spell(
    id=47201,
    name='Everlasting Affliction',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=47422),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=24),
    ],
    spell_icon_id=3169,
    notes='warlock-rework AFFLICTION §6 (9,1) / §7.3: eff2 op ADD_FLAT_MODIFIER(107)->ADD_PCT_MODIFIER(108), bp raised to 1 (2%), mask corrected to CORRUPTION_UA; ProcChance 20->33 (the stock load-time correction still OR-s Corruption into this effect index, SpellInfoCorrections.cpp, harmless). Trigger 47422 replaced with a pure RefreshDuration() (spell_warl_everlasting_affliction_refresh, unbind -47422 spell_warl_everlasting_affliction) - Howl of Terror added as a source (EVERLASTING_TRIGGER).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the spell damage scaling of your Corruption and Unstable Affliction by $s2%.  Your Drain Life, Drain Soul, Shadow Bolt, Haunt and Howl of Terror spells have a $h% chance to reset the duration of your Corruption spell on the target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': m.CORRUPTION_UA[0], 'EffectSpellClassMaskB_2': m.CORRUPTION_UA[1], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '1', 'Name_Lang_Mask': 16712190, 'ProcChance': 33, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 5},
)


everlasting_affliction_47202 = spell(
    id=47202,
    name='Everlasting Affliction',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=47422),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=24),
    ],
    spell_icon_id=3169,
    notes='warlock-rework AFFLICTION §6 (9,1): bp raised to 3 (4%), ProcChance 40->66.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the spell damage scaling of your Corruption and Unstable Affliction by $s2%.  Your Drain Life, Drain Soul, Shadow Bolt, Haunt and Howl of Terror spells have a $h% chance to reset the duration of your Corruption spell on the target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': m.CORRUPTION_UA[0], 'EffectSpellClassMaskB_2': m.CORRUPTION_UA[1], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '2', 'Name_Lang_Mask': 16712190, 'ProcChance': 66, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 5},
)


everlasting_affliction_47203 = spell(
    id=47203,
    name='Everlasting Affliction',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=47422),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=24),
    ],
    spell_icon_id=3169,
    notes='warlock-rework AFFLICTION §6 (9,1): bp raised to 5 (6%), ProcChance 60->100.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the spell damage scaling of your Corruption and Unstable Affliction by $s2%.  Your Drain Life, Drain Soul, Shadow Bolt, Haunt and Howl of Terror spells have a $h% chance to reset the duration of your Corruption spell on the target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': m.CORRUPTION_UA[0], 'EffectSpellClassMaskB_2': m.CORRUPTION_UA[1], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 5},
)
scripted_by(47422, 'spell_warl_everlasting_affliction_refresh')
unbind_script(47422, 'spell_warl_everlasting_affliction')
procs_on(-47201, proc_flags=0x10000, family_name=5, family_mask=m.EVERLASTING_TRIGGER, spell_type_mask=m.PROC_SPELL_TYPE_MASK_ALL, spell_phase_mask=m.PROC_SPELL_PHASE_HIT, chance=0, cooldown_ms=0)


everlasting_affliction_47204 = spell(
    id=47204,
    name='Everlasting Affliction',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=47422),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=107, misc_value=24),
    ],
    spell_icon_id=3169,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Corruption and Unstable Affliction spells gain an additional $s2% of your bonus spell damage, and your Drain Life, Drain Soul, Shadow Bolt, and Haunt spells have a $h% chance to reset the duration of your Corruption spell on the target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_2': 257, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '4', 'Name_Lang_Mask': 16712190, 'ProcChance': 80, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 5},
)


everlasting_affliction_47205 = spell(
    id=47205,
    name='Everlasting Affliction',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=47422),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=107, misc_value=24),
    ],
    spell_icon_id=3169,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Corruption and Unstable Affliction spells gain an additional $s2% of your bonus spell damage, and your Drain Life, Drain Soul, Shadow Bolt, and Haunt spells have a $h% chance to reset the duration of your Corruption spell on the target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_2': 257, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '5', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 5},
)


empowered_imp_47220 = spell(
    id=47220,
    name='Empowered Imp',
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
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=3171,
    notes='warlock-rework DESTRUCTION §6 (8,2): eff1 rewritten from ADD_FLAT_MODIFIER CHANCE_OF_SUCCESS (stock 54278 proc chance mod) to ADD_PCT_MODIFIER CRIT_DAMAGE_BONUS (+33/66/100%), bp unchanged, mask -> B_1 IMP_FIREBOLT (0x1000). Removing the CHANCE_OF_SUCCESS mod leaves 54278s proc at its DBC chance 0 -> inert.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage done by your Imp's Firebolt by $s1% and its critical strike damage bonus by $s2%.\n\n|cFF9D9D9DCapstone Bonus: Your Imp's Firebolt has a 5% chance to make your next Soul Fire instant. Lasts 15 sec.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.IMP_FIREBOLT, 'EffectSpellClassMaskB_1': m.IMP_FIREBOLT, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


empowered_imp_47221 = spell(
    id=47221,
    name='Empowered Imp',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=65, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=3171,
    notes='warlock-rework DESTRUCTION §6 (8,2): see rank 1s note.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage done by your Imp's Firebolt by $s1% and its critical strike damage bonus by $s2%.\n\n|cFF9D9D9DCapstone Bonus: Your Imp's Firebolt has a 5% chance to make your next Soul Fire instant. Lasts 15 sec.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.IMP_FIREBOLT, 'EffectSpellClassMaskB_1': m.IMP_FIREBOLT, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassSet': 5},
)


empowered_imp_47223 = spell(
    id=47223,
    name='Empowered Imp',
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
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=3171,
    notes='warlock-rework DESTRUCTION §6 (8,2): r3 final rank, see rank 1s note; capstone script is spell_warl_empowered_imp on Firebolt 3110 (WP-B, §7.15) + the CanPrepare arbiter registration (§7.6).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage done by your Imp's Firebolt by $s1% and its critical strike damage bonus by $s2%.\n\nCapstone Bonus: Your Imp's Firebolt has a 5% chance to make your next Soul Fire instant. Lasts 15 sec.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.IMP_FIREBOLT, 'EffectSpellClassMaskB_1': m.IMP_FIREBOLT, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
scripted_by(3110, 'spell_warl_empowered_imp')


fel_synergy_47230 = spell(
    id=47230,
    name='Fel Synergy',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=8),
    ],
    spell_icon_id=3222,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You have a $h% chance to heal your pet for $s1% of the amount of spell damage done by you.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 67108864, 'EffectSpellClassMaskB_2': 16384, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'ProcTypeMask': 332096, 'RangeIndex': 1, 'SpellClassSet': 5},
)


fel_synergy_47231 = spell(
    id=47231,
    name='Fel Synergy',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3222,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You have a $h% chance to heal your pet for $s1% of the amount of spell damage done by you.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 67108864, 'EffectSpellClassMaskB_2': 16384, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 332096, 'RangeIndex': 1, 'SpellClassSet': 5},
)


demonic_pact_47236 = spell(
    id=47236,
    name='Demonic Pact',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=107, misc_value=18),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=79, misc_value=36),
    ],
    spell_icon_id=3220,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your spell damage by $s3%, and your pet's criticals apply the Demonic Pact effect to your party or raid members. Demonic Pact increases spell power by $s1% of your Spell Damage for $48090d. This effect has a $53646s2 sec cooldown. Does not work on Enslaved demons.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 524288, 'EffectSpellClassMaskB_2': 1048576, 'EffectSpellClassMaskC_1': 525799, 'EffectSpellClassMaskC_2': 8886738, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


demonic_pact_47237 = spell(
    id=47237,
    name='Demonic Pact',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=107, misc_value=18),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=79, misc_value=36),
    ],
    spell_icon_id=3220,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your spell damage by $s3%, and your pet's criticals apply the Demonic Pact effect to your party or raid members. Demonic Pact increases spell power by $s1% of your Spell Damage for $48090d. This effect has a $53646s2 sec cooldown. Does not work on Enslaved demons.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 524288, 'EffectSpellClassMaskB_2': 1048576, 'EffectSpellClassMaskC_1': 525799, 'EffectSpellClassMaskC_2': 8886738, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


demonic_pact_47238 = spell(
    id=47238,
    name='Demonic Pact',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=107, misc_value=18),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=79, misc_value=36),
    ],
    spell_icon_id=3220,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your spell damage by $s3%, and your pet's criticals apply the Demonic Pact effect to your party or raid members. Demonic Pact increases spell power by $s1% of your Spell Damage for $48090d. This effect has a $53646s2 sec cooldown. Does not work on Enslaved demons.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 524288, 'EffectSpellClassMaskB_2': 1048576, 'EffectSpellClassMaskC_1': 525799, 'EffectSpellClassMaskC_2': 8886738, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


demonic_pact_47239 = spell(
    id=47239,
    name='Demonic Pact',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=107, misc_value=18),
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=79, misc_value=36),
    ],
    spell_icon_id=3220,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your spell damage by $s3%, and your pet's criticals apply the Demonic Pact effect to your party or raid members. Demonic Pact increases spell power by $s1% of your Spell Damage for $48090d. This effect has a $53646s2 sec cooldown. Does not work on Enslaved demons.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 524288, 'EffectSpellClassMaskB_2': 1048576, 'EffectSpellClassMaskC_1': 525799, 'EffectSpellClassMaskC_2': 8886738, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


demonic_pact_47240 = spell(
    id=47240,
    name='Demonic Pact',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=107, misc_value=18),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=79, misc_value=36),
    ],
    spell_icon_id=3220,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your spell damage by $s3%, and your pet's criticals apply the Demonic Pact effect to your party or raid members. Demonic Pact increases spell power by $s1% of your Spell Damage for $48090d. This effect has a $53646s2 sec cooldown. Does not work on Enslaved demons.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 524288, 'EffectSpellClassMaskB_2': 1048576, 'EffectSpellClassMaskC_1': 525799, 'EffectSpellClassMaskC_2': 8886738, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


molten_core_47245 = spell(
    id=47245,
    name='Molten Core',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=4, trigger_spell=47383),
        Effect(type=EffectType.APPLY_AURA, base_points=2999, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=3175,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the duration of your Immolate by $/1000;47245s2 sec, and you have a $47245h% chance to gain the Molten Core effect when your Corruption deals damage. The Molten Core effect empowers your next 3 Incinerate or Soul Fire spells cast within $47383d.\r\n\r\nIncinerate - Increases damage done by $47383s1% and reduces cast time by $47383s3%.\r\n\r\nSoul Fire - Increases damage done by $47383s1% and increases critical strike chance by $47383s2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 4, 'ProcTypeMask': 327680, 'RangeIndex': 1, 'SpellClassSet': 5},
)


molten_core_47246 = spell(
    id=47246,
    name='Molten Core',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=71162),
        Effect(type=EffectType.APPLY_AURA, base_points=5999, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=3175,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the duration of your Immolate by $/1000;47246s2 sec, and you have a $47246h% chance to gain the Molten Core effect when your Corruption deals damage. The Molten Core effect empowers your next 3 Incinerate or Soul Fire spells cast within $71162d.\r\n\r\nIncinerate - Increases damage done by $71162s1% and reduces cast time by $71162s3%.\r\n\r\nSoul Fire - Increases damage done by $71162s1% and increases critical strike chance by $71162s2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 8, 'ProcTypeMask': 327680, 'RangeIndex': 1, 'SpellClassSet': 5},
)


molten_core_47247 = spell(
    id=47247,
    name='Molten Core',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=71165),
        Effect(type=EffectType.APPLY_AURA, base_points=8999, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=3175,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the duration of your Immolate by $/1000;47247s2 sec, and you have a $47247h% chance to gain the Molten Core effect when your Corruption deals damage. The Molten Core effect empowers your next 3 Incinerate or Soul Fire spells cast within $71165d.\r\n\r\nIncinerate - Increases damage done by $71165s1% and reduces cast time by $71165s3%.\r\n\r\nSoul Fire - Increases damage done by $71165s1% and increases critical strike chance by $71165s2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 12, 'ProcTypeMask': 262144, 'RangeIndex': 1, 'SpellClassSet': 5},
)


backdraft_47258 = spell(
    id=47258,
    name='Backdraft',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=7, trigger_spell=54274),
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=3170,
    notes='warlock-rework DESTRUCTION §6 (8,0): eff0 kept. New eff1 ADD_PCT_MODIFIER DAMAGE bp 6/13/19 (7/14/20%), B_1 = SHADOWBURN (0x80). CheckProc filter in spell_warl_backdraft (WP-B, §7.15) - Conflagrate, Shadowfury, Shadowburn, or priest Mind Blast (Classless); -47258 row -> family 0, CAST (§8).',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you cast Conflagrate, Mind Blast, Shadowfury or Shadowburn, the cast time and global cooldown of your next three Destruction spells are reduced by $54274s1%. Lasts $54274d. Increases the damage of your Shadowburn by $s2%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 516, 'EffectSpellClassMaskA_2': 65536, 'EffectSpellClassMaskB_1': m.SHADOWBURN, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 69632, 'RangeIndex': 1, 'SpellClassSet': 5},
)


backdraft_47259 = spell(
    id=47259,
    name='Backdraft',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=7, trigger_spell=54276),
        Effect(type=EffectType.APPLY_AURA, base_points=13, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=3170,
    notes='warlock-rework DESTRUCTION §6 (8,0): see rank 1s note.',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you cast Conflagrate, Mind Blast, Shadowfury or Shadowburn, the cast time and global cooldown of your next three Destruction spells are reduced by $54276s1%. Lasts $54276d. Increases the damage of your Shadowburn by $s2%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 516, 'EffectSpellClassMaskA_2': 65536, 'EffectSpellClassMaskB_1': m.SHADOWBURN, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 5},
)


backdraft_47260 = spell(
    id=47260,
    name='Backdraft',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=7, trigger_spell=54277),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=3170,
    notes='warlock-rework DESTRUCTION §6 (8,0): r3 final rank, see rank 1s note.',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you cast Conflagrate, Mind Blast, Shadowfury or Shadowburn, the cast time and global cooldown of your next three Destruction spells are reduced by $54277s1%. Lasts $54277d. Increases the damage of your Shadowburn by $s2%.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 516, 'EffectSpellClassMaskA_2': 65536, 'EffectSpellClassMaskB_1': m.SHADOWBURN, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 5},
)
scripted_by(47258, 'spell_warl_backdraft')
scripted_by(47259, 'spell_warl_backdraft')
scripted_by(47260, 'spell_warl_backdraft')
procs_on(-47258, proc_flags=m.PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG, family_name=0, spell_type_mask=0, spell_phase_mask=m.PROC_SPELL_PHASE_CAST, chance=100, cooldown_ms=0)


fire_and_brimstone_47266 = spell(
    id=47266,
    name='Fire and Brimstone',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=107, misc_value=23),
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=3173,
    notes='warlock-rework DESTRUCTION §6 (9,1): eff0 rewritten from DUMMY (stock C4 key icon 3173) to ADD_FLAT_MODIFIER EFFECT3 (SPELLMOD_EFFECT3, adds to Immolate 348 eff2s aura-271 amount) bp 2/5/9 (+3/6/10), A_1 = IMMOLATE (0x4). eff1 bp 4/9/14 -> 7/15/24 (8/16/25%), mask -> B_2 CONFLAGRATE (0x800000).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Incinerate, Searing Pain, Soul Fire and Chaos Bolt spells to targets afflicted by your Immolate by $s1%. Increases the critical strike chance of your Conflagrate by $s2%.\n\n|cFF9D9D9DCapstone Bonus: Your Fire spells with a cast time that deal direct damage increase the damage the target takes from your next Soul Fire by 5%. Stacks up to 10. Incinerate generates 2 stacks. Soul Fire does not generate stacks.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.IMMOLATE, 'EffectSpellClassMaskB_2': m.CONFLAGRATE, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


fire_and_brimstone_47267 = spell(
    id=47267,
    name='Fire and Brimstone',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=107, misc_value=23),
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=3173,
    notes='warlock-rework DESTRUCTION §6 (9,1): see rank 1s note.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Incinerate, Searing Pain, Soul Fire and Chaos Bolt spells to targets afflicted by your Immolate by $s1%. Increases the critical strike chance of your Conflagrate by $s2%.\n\n|cFF9D9D9DCapstone Bonus: Your Fire spells with a cast time that deal direct damage increase the damage the target takes from your next Soul Fire by 5%. Stacks up to 10. Incinerate generates 2 stacks. Soul Fire does not generate stacks.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.IMMOLATE, 'EffectSpellClassMaskB_2': m.CONFLAGRATE, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


fire_and_brimstone_47268 = spell(
    id=47268,
    name='Fire and Brimstone',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=23),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=107, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200990),
    ],
    spell_icon_id=3173,
    notes='warlock-rework DESTRUCTION §6 (9,1): r3 final rank, bp 9/24; new eff2 PROC_TRIGGER_SPELL -> 200990 (never DUMMY - C4 keys on a caster DUMMY aura on icon 3173, so the capstone marker must not be one; row in §8: fam 0, school Fire, chance 100).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Incinerate, Searing Pain, Soul Fire and Chaos Bolt spells to targets afflicted by your Immolate by $s1%. Increases the critical strike chance of your Conflagrate by $s2%.\n\nCapstone Bonus: Your Fire spells with a cast time that deal direct damage increase the damage the target takes from your next Soul Fire by 5%. Stacks up to 10. Incinerate generates 2 stacks. Soul Fire does not generate stacks.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.IMMOLATE, 'EffectSpellClassMaskB_2': m.CONFLAGRATE, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
scripted_by(fire_and_brimstone_47268, 'spell_warl_fire_and_brimstone')
procs_on(fire_and_brimstone_47268, proc_flags=m.PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG, family_name=0, school_mask=4, spell_type_mask=m.PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=m.PROC_SPELL_PHASE_HIT, chance=100, cooldown_ms=0, disable_effects_mask=0x3)


fire_and_brimstone_47269 = spell(
    id=47269,
    name='Fire and Brimstone',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=24),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=3173,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Incinerate and Chaos Bolt spells to targets afflicted by your Immolate by $s1%, and the critical strike chance of your Conflagrate spell is increased by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4, 'EffectSpellClassMaskB_2': 8388608, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


fire_and_brimstone_47270 = spell(
    id=47270,
    name='Fire and Brimstone',
    school=School.NORMAL,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=24),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=3173,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Incinerate and Chaos Bolt spells to targets afflicted by your Immolate by $s1%, and the critical strike chance of your Conflagrate spell is increased by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4, 'EffectSpellClassMaskB_2': 8388608, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_fear_53754 = spell(
    id=53754,
    name='Improved Fear',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=3),
    ],
    spell_icon_id=98,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Causes your Fear spell to inflict a Nightmare on the target when the fear effect ends. The Nightmare effect reduces the target's movement speed by $60946s1% for $60946d.", 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 32768, 'EffectSpellClassMaskB_2': 2097152, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'ProcTypeMask': 69632, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_fear_53759 = spell(
    id=53759,
    name='Improved Fear',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=3),
    ],
    spell_icon_id=98,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Causes your Fear spell to inflict a Nightmare on the target when the fear effect ends. The Nightmare effect reduces the target's movement speed by $60947s1% for $60947d.", 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 32768, 'EffectSpellClassMaskB_2': 2097152, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87040, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_felhunter_54037 = spell(
    id=54037,
    name='Improved Felhunter',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=5000),
    ],
    spell_icon_id=2027,
    notes="warlock-rework AFFLICTION §6 (5,3): rewritten - icon 214->2027 (makes the stock icon-214 Shadow Bite mana hardcode inert, C13/B17c); eff1 now a plain -10% cooldown SpellMod on Devour Magic/Spell Lock (FELHUNTER_UTILITY); eff2 is a 5s tick read by spell_warl_improved_felhunter to apply the pet damage buff 200771; old Fel Intelligence effects dropped.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage of your Felhunter by $s2%.  Reduces the cooldown of your Felhunter's Devour Magic and Spell Lock by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Your Felhunter's Shadow Bite cooldown is reduced by 4 sec, and it also restores 10% of its mana when used.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_3': m.FELHUNTER_UTILITY[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_felhunter_54038 = spell(
    id=54038,
    name='Improved Felhunter',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=5000),
        Effect(type=EffectType.APPLY_AURA, base_points=-4001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=2027,
    notes='warlock-rework AFFLICTION §6 (5,3) capstone: eff3 (new) flat -4s cooldown on Shadow Bite (6s -> 2s); the 10% mana clause is spell_warl_shadow_bite_improved_felhunter (B17c, 54049-54053).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage of your Felhunter by $s2%.  Reduces the cooldown of your Felhunter's Devour Magic and Spell Lock by $s1%.\n\nCapstone Bonus: Your Felhunter's Shadow Bite cooldown is reduced by 4 sec, and it also restores 10% of its mana when used.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_3': m.FELHUNTER_UTILITY[2], 'EffectSpellClassMaskC_2': m.SHADOW_BITE, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
scripted_by(improved_felhunter_54037, 'spell_warl_improved_felhunter')
scripted_by(improved_felhunter_54038, 'spell_warl_improved_felhunter')


improved_soul_leech_54117 = spell(
    id=54117,
    name='Improved Soul Leech',
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
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3176,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Soul Leech effect also restores mana to you and your summoned demon equal to $s1% of maximum mana, and has a $s2% chance to grant up to 10 party or raid members mana regeneration equal to 1% of maximum mana per 5 sec. Lasts for $57669d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 897, 'EffectSpellClassMaskA_2': 192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_soul_leech_54118 = spell(
    id=54118,
    name='Improved Soul Leech',
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
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3176,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Soul Leech effect also restores mana to you and your summoned demon equal to $s1% of maximum mana, and has a $s2% chance to grant up to 10 party or raid members mana regeneration equal to 1% of maximum mana per 5 sec. Lasts for $57669d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 897, 'EffectSpellClassMaskA_2': 192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_demonic_tactics_54347 = spell(
    id=54347,
    name='Improved Demonic Tactics',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=15),
    ],
    spell_icon_id=3177,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your summoned demon's critical strike chance equal to $s1% of your critical strike chance.", 'EffectBasePoints_2': -1, 'EffectBasePoints_3': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 524773, 'EffectSpellClassMaskA_2': 8884224, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_demonic_tactics_54348 = spell(
    id=54348,
    name='Improved Demonic Tactics',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=15),
    ],
    spell_icon_id=3177,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your summoned demon's critical strike chance equal to $s1% of your critical strike chance.", 'EffectBasePoints_2': -1, 'EffectBasePoints_3': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 524773, 'EffectSpellClassMaskA_2': 8884224, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


improved_demonic_tactics_54349 = spell(
    id=54349,
    name='Improved Demonic Tactics',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=15),
    ],
    spell_icon_id=3177,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your summoned demon's critical strike chance equal to $s1% of your critical strike chance.", 'EffectBasePoints_2': -1, 'EffectBasePoints_3': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 524773, 'EffectSpellClassMaskA_2': 8884224, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


pandemic_58435 = spell(
    id=58435,
    name='Pandemic',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=22),
    ],
    spell_icon_id=2042,
    notes='warlock-rework AFFLICTION §6 (8,2): rewritten - stock periodic-crit (eff1) and crit-damage SpellMod (eff2, SYSTEM §14) both removed; single new eff1 is a flat +5% Unstable Affliction damage SpellMod (talent rank count 1->2, new rank 200768 below adds the carry-duration capstone).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage of your Unstable Affliction by $s1%.  Applying Unstable Affliction during its final 5 sec adds the remaining time to its new duration.\n\n|cFF9D9D9DCapstone Bonus: Your Unstable Affliction's damage is increased by your Mastery.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 0, 'EffectSpellClassMaskA_2': 256, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


pandemic_200768 = spell(
    id=200768,
    name='Pandemic',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=22),
    ],
    spell_icon_id=2042,
    notes='warlock-rework AFFLICTION §6 (8,2): new rank 2 (bp 4->9, 5%->10%); capstone: Unstable Afflictions damage is increased by Mastery (script only, spell_warl_unstable_affliction_affliction DoEffectCalcAmount, HasAura(200768)).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage of your Unstable Affliction by $s1%.  Applying Unstable Affliction during its final 5 sec adds the remaining time to its new duration.\n\nCapstone Bonus: Your Unstable Affliction's damage is increased by your Mastery.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 0, 'EffectSpellClassMaskA_2': 256, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


metamorphosis_59672 = spell(
    id=59672,
    name='Metamorphosis',
    school=School.NORMAL,
    attributes=8388992,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.LEARN_SPELL, die_sides=0, implicit_target_a=1, trigger_spell=47241),
        Effect(type=EffectType.LEARN_SPELL, base_points=-1, implicit_target_a=1, trigger_spell=50581),
        Effect(type=EffectType.LEARN_SPELL, base_points=-1, implicit_target_a=1, trigger_spell=59673),
    ],
    spell_icon_id=3314,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 2147483648, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "You transform into a Demon for $47241d.  This form increases your armor by $47241s2%, damage by $47241s3%, reduces the chance you'll be critically hit by melee attacks by 6% and reduces the duration of stun and snare effects by $54817s1%.  You gain some unique demon abilities in addition to your normal abilities. 3 minute cooldown.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 67108864, 'EffectSpellClassMaskB_2': 16384, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


ruin_59738 = spell(
    id=59738,
    name='Ruin',
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
    spell_icon_id=234,
    notes='warlock-rework DESTRUCTION §6 (5,2), A1/A2 (SHARED §1.1): r2 eff0 stock ADD_PCT_MODIFIER CRIT_DAMAGE_BONUS zeroed (type -> APPLY_AURA DUMMY, bp 0, die_sides 0, A masks cleared), replaced by linked_spell(59738, 200702, 2) - 180% at this rank.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spell critical strikes now deal 180% damage. This does not stack with other similar effects.\n\n|cFF9D9D9DCapstone Bonus: Increases your Fire and Shadow damage done by 3%. This effect is quadrupled against targets above 75% health.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 0, 'EffectSpellClassMaskA_2': 0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
linked_spell(59738, 200702, type=2)


ruin_59739 = spell(
    id=59739,
    name='Ruin',
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
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=36),
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_DONE_VERSUS_AURASTATE, misc_value=23),
    ],
    spell_icon_id=234,
    notes='warlock-rework DESTRUCTION §6 (5,2), A1/A2: r3 final rank - eff0 zeroed, linked_spell(59739, 200703, 2) (200% display; stored amount 33 per A1). New eff1 MOD_DAMAGE_PERCENT_DONE misc 36 (Fire|Shadow) bp 2 (+3%); new eff2 MOD_DAMAGE_DONE_VERSUS_AURASTATE misc 23 (AURA_STATE_HEALTH_ABOVE_75_PERCENT) bp 8 (+9%, combined 1.03x1.09=+12.27%, §11 Q3) - Warlock::GetAuraStateDoneFactor reads this for the Rain of Fire snapshot correction (§7.1).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spell critical strikes now deal 200% damage. This does not stack with other similar effects.\n\nCapstone Bonus: Increases your Fire and Shadow damage done by 3%. This effect is quadrupled against targets above 75% health.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 0, 'EffectSpellClassMaskA_2': 0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
linked_spell(59739, 200703, type=2)


ruin_59740 = spell(
    id=59740,
    name='Ruin',
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
    spell_icon_id=234,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the critical strike damage bonus of your Destruction spells and your Imp's Firebolt spell by $s1%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 5093, 'EffectSpellClassMaskA_2': 12783808, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


ruin_59741 = spell(
    id=59741,
    name='Ruin',
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
    spell_icon_id=234,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the critical strike damage bonus of your Destruction spells and your Imp's Firebolt spell by $s1%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 5093, 'EffectSpellClassMaskA_2': 12783808, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


siphon_life_63108 = spell(
    id=63108,
    name='Siphon Life',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=152,
    notes='warlock-rework AFFLICTION §6 (4,0): bp 39/4 -> 1/1 (2%/2%); eff2 mask -> SIPHON_LIFE_DOT (adds Seed DoT, UA); ProcTypeMask 0x50000->0x40000 (periodic only, matches the leech-talent gate in spell_warl_siphon_life_affliction).',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you deal damage with your Corruption spell, you are instantly healed for $s1% of the damage done, to a maximum of 5% of your maximum health.  Your Corruption, Seed of Corruption and Unstable Affliction damage over time effects are increased by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskB_1': m.SIPHON_LIFE_DOT[0], 'EffectSpellClassMaskB_2': m.SIPHON_LIFE_DOT[1], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 262144, 'RangeIndex': 1, 'SpellClassSet': 5, 'SpellDescriptionVariableID': 83},
)
scripted_by(siphon_life_63108, 'spell_warl_siphon_life_affliction')
unbind_script(63108, 'spell_warl_siphon_life')
procs_on(siphon_life_63108, proc_flags=m.PROC_FLAG_DONE_PERIODIC, family_name=5, family_mask=(0x2, 0, 0), spell_type_mask=1, spell_phase_mask=m.PROC_SPELL_PHASE_HIT, chance=100, cooldown_ms=0)


siphon_life_200767 = spell(
    id=200767,
    name='Siphon Life',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=152,
    notes='warlock-rework AFFLICTION §6 (4,0): new rank 2 (talent 1041 rank count 1->2, PLAN §1); 4%/4%.',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you deal damage with your Corruption spell, you are instantly healed for $s1% of the damage done, to a maximum of 5% of your maximum health.  Your Corruption, Seed of Corruption and Unstable Affliction damage over time effects are increased by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskB_1': m.SIPHON_LIFE_DOT[0], 'EffectSpellClassMaskB_2': m.SIPHON_LIFE_DOT[1], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 262144, 'RangeIndex': 1, 'SpellClassSet': 5, 'SpellDescriptionVariableID': 83},
)
scripted_by(siphon_life_200767, 'spell_warl_siphon_life_affliction')
procs_on(siphon_life_200767, proc_flags=m.PROC_FLAG_DONE_PERIODIC, family_name=5, family_mask=(0x2, 0, 0), spell_type_mask=1, spell_phase_mask=m.PROC_SPELL_PHASE_HIT, chance=100, cooldown_ms=0)


nemesis_63117 = spell(
    id=63117,
    name='Nemesis',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=108, misc_value=11),
    ],
    spell_icon_id=3315,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Demonic Empowerment, Metamorphosis, and Fel Domination spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_3': 12416, 'EffectSpellClassMaskB_1': 576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


nemesis_63121 = spell(
    id=63121,
    name='Nemesis',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=108, misc_value=11),
    ],
    spell_icon_id=3315,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Demonic Empowerment, Metamorphosis, and Fel Domination spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_3': 12416, 'EffectSpellClassMaskB_1': 576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


nemesis_63123 = spell(
    id=63123,
    name='Nemesis',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=108, misc_value=11),
    ],
    spell_icon_id=3315,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Demonic Empowerment, Metamorphosis, and Fel Domination spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_3': 12416, 'EffectSpellClassMaskB_1': 576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


decimation_63156 = spell(
    id=63156,
    name='Decimation',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=8, trigger_spell=63165),
        Effect(type=EffectType.APPLY_AURA, base_points=34, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=184,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you Shadowbolt, Incinerate or Soul Fire a target that is at or below $s2% health, the cast time of Soul Fire spell is reduced by $s1% for $63165d. Soul Fires cast under the effect of Decimation cost no shard.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 67108864, 'EffectSpellClassMaskB_2': 16384, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 5},
)


decimation_63158 = spell(
    id=63158,
    name='Decimation',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=8, trigger_spell=63167),
        Effect(type=EffectType.APPLY_AURA, base_points=34, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=184,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you Shadowbolt, Incinerate or Soul Fire a target that is at or below $63158s2% health, the cast time of your Soul Fire spell is reduced by $63158s1% for $63165d. Soul Fires cast under the effect of Decimation cost no shard.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 67108864, 'EffectSpellClassMaskB_2': 16384, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 69632, 'RangeIndex': 1, 'SpellClassSet': 5},
)


pyroclasm_63245 = spell(
    id=63245,
    name='Pyroclasm',
    school=School.FIRE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=2189, trigger_spell=63244),
    ],
    spell_icon_id=1137,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you critically strike with Searing Pain, Scorch, or Conflagrate, your Fire and Shadow spell damage is increased by $63244s1% for $63244d.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 576, 'EffectSpellClassMaskA_2': 8388736, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 5},
)
scripted_by(pyroclasm_63245, 'spell_warl_pyroclasm')



shadow_trance_17941 = spell(
    id=17941,
    name='Shadow Trance',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    attributes=151060480,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=10),
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=0),
    ],
    spell_icon_id=164,
    notes='warlock-rework AFFLICTION §7.5: Nightfall/Soulburn: Seed instant-cast buff, rewritten with 3 effects - eff1 -100% cast time (kept), new eff2 -50% cost, new eff3 0% damage bonus (BP2 overrides the live 5/10/15% from the granting Nightfall rank at cast, §7 header). All three masked SHADOW_TRANCE_CONSUMERS = (SHADOW_BOLT, SEED_OF_CORRUPTION_DOT, 0) except eff3 which stays Shadow Bolt only (letters A/B/C = effect index 1/2/3 per the EffectSpellClassMask gotcha - eff2s mask goes on the B letter, eff3s on C).',
    raw_overrides={'AttributesEx4': 512, 'AttributesEx6': 64, 'CastingTimeIndex': 1, 'ProcChance': 101, 'ProcCharges': 1, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': m.SHADOW_TRANCE_CONSUMERS[0], 'EffectSpellClassMaskA_2': m.SHADOW_TRANCE_CONSUMERS[1], 'EffectSpellClassMaskB_1': m.SHADOW_TRANCE_CONSUMERS[0], 'EffectSpellClassMaskB_2': m.SHADOW_TRANCE_CONSUMERS[1], 'EffectSpellClassMaskC_1': m.SHADOW_BOLT, 'SpellVisualID_1': 5219, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Your next Shadow Bolt or Seed of Corruption becomes an instant cast and costs 50% less mana.  That Shadow Bolt deals increased damage.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next Shadow Bolt or Seed of Corruption is instant and costs 50% less mana.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 5, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)
procs_on(shadow_trance_17941, proc_flags=0x10000, family_name=5, family_mask=m.SHADOW_TRANCE_CONSUMERS, spell_type_mask=1, spell_phase_mask=m.PROC_SPELL_PHASE_CAST, attributes_mask=m.PROC_ATTR_REQ_SPELLMOD, chance=0, cooldown_ms=0)


shadowburn_29341 = spell(
    id=29341,
    name='Shadowburn',
    school=School.SHADOW,
    attributes=134283264,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, die_sides=0, implicit_target_a=6, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1590,
    notes='warlock-rework AFFLICTION §4.2 B9/§7.10: eff1 aura 86 (CHANNEL_DEATH_ITEM) replaced by DUMMY - shard generation moves to the Soul Shard buff (200709), granted by spell_warl_shadowburn_shard on kill.',
    raw_overrides={'AttributesEx': 136, 'AttributesEx2': 4, 'CastingTimeIndex': 1, 'ProcChance': 101, 'SpellLevel': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712174, 'Description_Lang_enUS': 'Instantly blasts the target with Shadow damage.  If the target dies within $29341d of Shadowburn, and yields experience or honor, you gain a Soul Shard.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'If target dies, casting warlock gets a Soul Shard.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 5, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_3': 1.0},
)
scripted_by(shadowburn_29341, 'spell_warl_shadowburn_shard')
unbind_script(29341, 'spell_warl_shadowburn')


shadow_embrace_32386 = spell(
    id=32386,
    name='Shadow Embrace',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=6, apply_aura=271, misc_value=32),
    ],
    spell_icon_id=2209,
    notes='warlock-rework AFFLICTION §4.6 row 8/§6 (4,3): duration 12->15s; mask -> SHADOW_PERIODIC; healing-reduction link to 60448 dropped (unlink_spell, §11 Q8) - tooltip no longer mentions it.',
    raw_overrides={'AttributesEx3': 196736, 'CastingTimeIndex': 1, 'AuraInterruptFlags': 524288, 'ProcChance': 101, 'CumulativeAura': 3, 'EquippedItemClass': -1, 'EffectDieSides_2': 1, 'EffectBasePoints_2': -1, 'EffectSpellClassMaskA_1': m.SHADOW_PERIODIC[0], 'EffectSpellClassMaskA_2': m.SHADOW_PERIODIC[1], 'EffectSpellClassMaskA_3': m.SHADOW_PERIODIC[2], 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'Your direct damage Shadow spells, Drain Life and Drain Soul apply Shadow Embrace, increasing all periodic Shadow damage you deal to the target by $32386s1% per stack. Lasts $d. Stacks up to $32386u times.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Periodic Shadow damage taken increased by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 5, 'SpellClassMask_1': 2147483648, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0},
)
unlink_spell(32386, 60448, 2)


shadow_embrace_32388 = spell(
    id=32388,
    name='Shadow Embrace',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=6, apply_aura=271, misc_value=32),
    ],
    spell_icon_id=2209,
    notes='warlock-rework AFFLICTION §4.6 row 8/§6 (4,3): see rank 1s note.',
    raw_overrides={'AttributesEx3': 196736, 'CastingTimeIndex': 1, 'AuraInterruptFlags': 524288, 'ProcChance': 101, 'CumulativeAura': 3, 'EquippedItemClass': -1, 'EffectDieSides_2': 1, 'EffectBasePoints_2': -1, 'EffectSpellClassMaskA_1': m.SHADOW_PERIODIC[0], 'EffectSpellClassMaskA_2': m.SHADOW_PERIODIC[1], 'EffectSpellClassMaskA_3': m.SHADOW_PERIODIC[2], 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'Your direct damage Shadow spells, Drain Life and Drain Soul apply Shadow Embrace, increasing all periodic Shadow damage you deal to the target by $32388s1% per stack. Lasts $d. Stacks up to $32386u times.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Periodic Shadow damage taken increased by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 5, 'SpellClassMask_1': 2147483648, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0},
)
unlink_spell(32388, 60465, 2)


shadow_embrace_32389 = spell(
    id=32389,
    name='Shadow Embrace',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=6, apply_aura=271, misc_value=32),
    ],
    spell_icon_id=2209,
    notes='warlock-rework AFFLICTION §4.6 row 9/§6 (4,3): stock inconsistency (this rank alone carried a different mask, (0x440E,0x111,0x2)) resolved onto the shared SHADOW_PERIODIC mask like ranks 1/2.',
    raw_overrides={'AttributesEx3': 196736, 'CastingTimeIndex': 1, 'AuraInterruptFlags': 524288, 'ProcChance': 101, 'CumulativeAura': 3, 'EquippedItemClass': -1, 'EffectDieSides_2': 1, 'EffectBasePoints_2': -1, 'EffectSpellClassMaskA_1': m.SHADOW_PERIODIC[0], 'EffectSpellClassMaskA_2': m.SHADOW_PERIODIC[1], 'EffectSpellClassMaskA_3': m.SHADOW_PERIODIC[2], 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'Your direct damage Shadow spells, Drain Life and Drain Soul apply Shadow Embrace, increasing all periodic Shadow damage you deal to the target by $32389s1% per stack. Lasts $d. Stacks up to $32386u times.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Periodic Shadow damage taken increased by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 5, 'SpellClassMask_1': 2147483648, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0},
)
unlink_spell(32389, 60466, 2)


# ---------------------------------------------------------------------------
# warlock-rework AFFLICTION pass - server-wide A1/A2 crit-damage exclusivity
# group (PLAN A1/A2, SHARED §1.1, AFFLICTION §4.8). Warlock's 9 of 27 hidden
# passives (Shadow Pact, Ruin, Fel Cruelty) live here - mage/priest/druid's
# own 18 are declared in their own trigger-spell files by this same pass.
# Ruin/Fel Cruelty's own talent ranks are Destruction's/Demonology's (not
# built this pass) - these passive rows exist now so the group is complete
# and those passes only need to add their own linked_spell() call.
# ---------------------------------------------------------------------------

def _crit_damage_passive(spell_id, name, stored_bp):
    return spell(
        id=spell_id, name=name, school=School.SHADOW, attributes=464,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
        range_yards=RANGE_SELF, duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, base_points=stored_bp, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_DAMAGE_BONUS, misc_value=126)],
        spell_icon_id=154,
        notes='warlock-rework AFFLICTION §4.8 (A1/A2, SHARED §1.1): hidden crit-damage passive, no visible icon/tooltip; joins spell_group 1201 (rule 3, highest only); linked (type=2) from its talent rank.',
        raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 5, 'EffectChainAmplitude_1': 1.0, 'AuraDescription_Lang_Mask': 16712188, 'Description_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101},
    )


shadow_pact_crit_200698 = _crit_damage_passive(200698, 'Shadow Pact', 9)
shadow_pact_crit_200699 = _crit_damage_passive(200699, 'Shadow Pact', 19)
shadow_pact_crit_200700 = _crit_damage_passive(200700, 'Shadow Pact', 32)
ruin_crit_200701 = _crit_damage_passive(200701, 'Ruin', 9)
ruin_crit_200702 = _crit_damage_passive(200702, 'Ruin', 19)
ruin_crit_200703 = _crit_damage_passive(200703, 'Ruin', 32)
fel_cruelty_crit_200704 = _crit_damage_passive(200704, 'Fel Cruelty', 9)
fel_cruelty_crit_200705 = _crit_damage_passive(200705, 'Fel Cruelty', 19)
fel_cruelty_crit_200706 = _crit_damage_passive(200706, 'Fel Cruelty', 32)

spell_group(
    1201,
    200680, 200681, 200682, 200683, 200684, 200685, 200686, 200687, 200688,
    200689, 200690, 200691, 200692, 200693, 200694, 200695, 200696, 200697,
    shadow_pact_crit_200698, shadow_pact_crit_200699, shadow_pact_crit_200700,
    ruin_crit_200701, ruin_crit_200702, ruin_crit_200703,
    fel_cruelty_crit_200704, fel_cruelty_crit_200705, fel_cruelty_crit_200706,
)
spell_group_rule(1201, 3, 'Spell crit damage talents - highest only (A1)')


# ---------------------------------------------------------------------------
# warlock-rework AFFLICTION pass - A3 Reach exclusivity passives (SHARED
# §1.2). Both ranks of Grim Reach (this pass, warlock_trigger_spells.py
# above) and Destructive Reach (Destruction, S2) link to these same two ids.
# ---------------------------------------------------------------------------

reach_200707 = spell(
    id=200707, name='Reach', school=School.SHADOW, attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=5)],
    spell_icon_id=1614,
    notes='warlock-rework AFFLICTION §5/§11 Q17 (A3, SHARED §1.2): hidden +3 yd range passive shared by Grim Reach r1 and Destructive Reach r1 (same caster, same spell id -> one aura, not additive). REACH_SPELLS = every warlock damaging spell with a target range.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 5, 'EffectChainAmplitude_1': 1.0, 'AuraDescription_Lang_Mask': 16712188, 'Description_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'EffectSpellClassMaskA_1': m.REACH_SPELLS[0], 'EffectSpellClassMaskA_2': m.REACH_SPELLS[1], 'EffectSpellClassMaskA_3': m.REACH_SPELLS[2]},
)


reach_200708 = spell(
    id=200708, name='Reach', school=School.SHADOW, attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=5)],
    spell_icon_id=1614,
    notes='warlock-rework AFFLICTION §5/§11 Q17 (A3, SHARED §1.2): hidden +6 yd range passive shared by Grim Reach r2 and Destructive Reach r2.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 5, 'EffectChainAmplitude_1': 1.0, 'AuraDescription_Lang_Mask': 16712188, 'Description_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'EffectSpellClassMaskA_1': m.REACH_SPELLS[0], 'EffectSpellClassMaskA_2': m.REACH_SPELLS[1], 'EffectSpellClassMaskA_3': m.REACH_SPELLS[2]},
)


# ---------------------------------------------------------------------------
# warlock-rework AFFLICTION pass - Soul Shards / Soulburn shared plumbing
# (SHARED §1.3, PLAN §6.4). Soulburn itself (200710, player-castable) is in
# warlock_spells.py; these three are never directly cast.
# ---------------------------------------------------------------------------

soul_shard_buff_200709 = spell(
    id=200709, name='Soul Shard', school=School.SHADOW, attributes=2147483648,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=120000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=1000),
    ],
    spell_icon_id=92,
    notes='warlock-rework AFFLICTION §5/§7.10 (B9): stacking buff, max 5 (CumulativeAura); each shard independently expires 120s after being gained (Warlock::GrantSoulShard/ConsumeSoulShards, per-player deque); the 1s tick (eff2) resyncs the stack count. NO_AURA_CANCEL (raw attributes=0x80000000) - not player-cancellable; no ALLOW_AURA_WHILE_DEAD/DEATH_PERSISTENT so it is removed on death (§11 Q9, shards drop on death via Warlock::ClearSoulShards in the AfterEffectRemove(BY_DEATH) handler).',
    raw_overrides={'AttributesEx4': 4, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Soul Shards, up to $u. Each shard fades 120 sec after it was gained.', 'CastingTimeIndex': 1, 'CumulativeAura': 5, 'DefenseType': 0, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Soul Shards.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 0, 'ProcChance': 101, 'SpellClassSet': 5, 'SpellPriority': 50},
)
scripted_by(soul_shard_buff_200709, 'spell_warl_soul_shard_buff')


soulburn_marker_200711 = spell(
    id=200711, name='Soulburn', school=School.SHADOW, attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=20000,
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY)],
    spell_icon_id=816,
    notes='warlock-rework AFFLICTION §5/§7.11 (SHARED §1.3, corrected to 20s): the "next cast is empowered" marker applied by Soulburn (200710); consumed by Warlock::TryConsumeSoulburnMarker (Seed of Corruption/Haunt this pass; Destruction adds Chaos Bolt/Soul Fire in S2).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next Seed of Corruption or Haunt is empowered.', 'CastingTimeIndex': 1, 'DefenseType': 0, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Soulburn marker.', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 0, 'ProcChance': 101, 'SpellClassSet': 5, 'SpellPriority': 50},
)


soulburn_haunt_debuff_200712 = spell(
    id=200712, name='Soulburn: Haunt', school=School.SHADOW, dispel=DispelType.MAGIC,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0, duration_ms=12000,
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=6, apply_aura=AuraType.MOD_DAMAGE_FROM_CASTER)],
    spell_icon_id=3172,
    notes='warlock-rework AFFLICTION §5/§7.13: applied by Haunt (48181) in addition to its own aura-271 effect only when Haunt consumes the Soulburn marker; the two live auras multiply to 44% (1.2 x 1.2, §0.2 item 5).',
    raw_overrides={'AttributesEx3': 65536, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': "Damage taken from the Warlock's Shadow damage-over-time effects increased by $s1%.", 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Soulburn: Haunt.', 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': m.SHADOW_PERIODIC[0], 'EffectSpellClassMaskA_2': m.SHADOW_PERIODIC[1], 'EffectSpellClassMaskA_3': m.SHADOW_PERIODIC[2], 'EquippedItemClass': -1, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 5, 'SpellPriority': 50},
)


# ---------------------------------------------------------------------------
# warlock-rework AFFLICTION pass - Bane of Agony's stack aura (§5/§7.2). The
# real Bane of Agony spell (980, renamed) is in warlock_spells.py; this is
# the separate per-target stack tracker Warlock::AddAgonyStacks reads.
# ---------------------------------------------------------------------------

bane_of_agony_stacks_200720 = spell(
    id=200720, name='Bane of Agony', school=School.SHADOW,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0, duration_ms=60000,
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=6, apply_aura=AuraType.DUMMY)],
    spell_icon_id=544,
    notes='warlock-rework AFFLICTION §5/§7.2: per-caster stack tracker for Bane of Agony (980) - CumulativeAura 15 (max cap with Improved Curses r2), refreshed by Warlock::AddAgonyStacks on each Bane tick; DOT_STACKING_RULE (AttributesEx3 0x80) so stacks are tracked per caster.',
    raw_overrides={'AttributesEx3': 128, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Bane of Agony damage increased by 10% per stack.', 'CastingTimeIndex': 1, 'CumulativeAura': 15, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Bane of Agony stacks.', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 5, 'SpellPriority': 50},
)


# ---------------------------------------------------------------------------
# warlock-rework AFFLICTION pass - Tainted Soul (Shadow Pact r3 capstone,
# §5/§6 (5,0)/§7.15).
# ---------------------------------------------------------------------------

tainted_soul_200721 = spell(
    id=200721, name='Tainted Soul', school=School.SHADOW,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0, duration_ms=30000,
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=6, apply_aura=AuraType.DUMMY)],
    spell_icon_id=207,
    notes='warlock-rework AFFLICTION §5/§7.15: per-caster stack tracker (CumulativeAura 10); Corruption applies 1 stack per crit tick, Bane of Agony/Unstable Affliction 2; erupts (200722) and clears at 10 stacks or on target death.',
    raw_overrides={'AttributesEx3': 128, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Tainted Soul.', 'CastingTimeIndex': 1, 'CumulativeAura': 10, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Tainted Soul stacks.', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 5, 'SpellPriority': 50},
)
scripted_by(tainted_soul_200721, 'spell_warl_tainted_soul')


tainted_soul_eruption_200722 = spell(
    id=200722, name='Tainted Soul', school=School.SHADOW,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0, radius_yards=6.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=57, points_per_level=1.6666666666666667, implicit_target_a=87, implicit_target_b=16, radius_yards=6.0),
        Effect(type=EffectType.DUMMY, base_points=100, die_sides=0, implicit_target_a=87),
    ],
    spell_icon_id=207,
    notes='warlock-rework AFFLICTION §5/§7.15: eruption, anchored at Shadow Pact row-5 level 35 (58@35, 99@60, 133@80); eff2 carries the erupt-percent (100 on a stack-cap eruption, 10*stacks on a death eruption) as a raw (die_sides=0) value read via GetSpellValue()->EffectBasePoints[EFFECT_1], scaling eff1s dealt damage. Target-select trims to the source unit + up to 4 others within 6 yd (QA #13/#14).',
    raw_overrides={'AttributesEx3': 65536, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Tainted Soul erupts, dealing Shadow damage to the target and up to 4 other enemies within 6 yards.', 'EffectBonusMultiplier_1': 0.4, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'MaxTargets': 5, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_3': m.TAINTED_SOUL, 'SpellClassSet': 5, 'SpellLevel': 35, 'BaseLevel': 35, 'SpellVisualID_1': 8339},
)
scripted_by(tainted_soul_eruption_200722, 'spell_warl_tainted_soul_eruption')


inevitable_demise_200723 = spell(
    id=200723, name='Inevitable Demise', school=School.SHADOW,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=30000,
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.DUMMY)],
    spell_icon_id=153,
    notes='warlock-rework AFFLICTION §5/§6 (1,3) Siphon Power capstone: stacks up to 50 (CumulativeAura), 5% per stack, consumed entirely by the next Drain Life (Warlock::AffLocal Drain Life script, §7.19).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next Drain Life deals $s1% more damage per stack.', 'CastingTimeIndex': 1, 'CumulativeAura': 50, 'DefenseType': 0, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Inevitable Demise.', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 0, 'ProcChance': 101, 'SpellClassSet': 5, 'SpellPriority': 50},
)


# ---------------------------------------------------------------------------
# warlock-rework AFFLICTION pass - Grim Reach r2 capstone (§5/§6 (3,1)).
# ---------------------------------------------------------------------------

grim_reach_debuff_200724 = spell(
    id=200724, name='Grim Reach', school=School.SHADOW, dispel=DispelType.MAGIC,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0, duration_ms=6000,
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=6, apply_aura=AuraType.MOD_DAMAGE_FROM_CASTER)],
    spell_icon_id=1614,
    notes='warlock-rework AFFLICTION §5/§6 (3,1): capstone debuff, refreshes rather than stacking (no CumulativeAura); masked WARLOCK_SHADOW_DAMAGE.',
    raw_overrides={'AttributesEx3': 65536, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Shadow damage taken from the Warlock increased by $s1%.', 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Grim Reach.', 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': m.WARLOCK_SHADOW_DAMAGE[0], 'EffectSpellClassMaskA_2': m.WARLOCK_SHADOW_DAMAGE[1], 'EffectSpellClassMaskA_3': m.WARLOCK_SHADOW_DAMAGE[2], 'EquippedItemClass': -1, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 5, 'SpellPriority': 50},
)


grim_reach_bolt_200725 = spell(
    id=200725, name='Grim Reach', school=School.SHADOW,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=49, points_per_level=3.5, implicit_target_a=6)],
    spell_icon_id=1614,
    notes='warlock-rework AFFLICTION §5/§6 (3,1): anchored at "50 at level 25, +3.5/level" -> 172@60, 242@80.',
    raw_overrides={'AttributesEx3': 65536, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Grim Reach bolt.', 'EffectBonusMultiplier_1': 0.35, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_3': m.GRIM_REACH_BOLT, 'SpellClassSet': 5, 'SpellLevel': 25, 'BaseLevel': 25, 'SpellVisualID_1': 8339},
)


# ---------------------------------------------------------------------------
# warlock-rework AFFLICTION pass - flat-SP % buffs shared by Improved Life
# Tap r3 (§6 (1,1)) and Siphon Power (§6 (1,3)) - PLAN §1A / SYSTEMS §15a.
# ---------------------------------------------------------------------------

improved_life_tap_buff_200726 = spell(
    id=200726, name='Improved Life Tap', school=School.SHADOW,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_DONE, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.MOD_HEALING_DONE, misc_value=126),
    ],
    spell_icon_id=208,
    notes='warlock-rework AFFLICTION §5/§7.8 (druid C1 shape): DoEffectCalcAmount computes 10% of the casters current spell power at apply (spell_warl_spell_power_pct_buff) - coefficient-only by construction.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Spell power increased by 10%.', 'CastingTimeIndex': 1, 'DefenseType': 0, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Using Life Tap increases your spell power by 10% for 15 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 0, 'ProcChance': 101, 'SpellClassSet': 5, 'SpellPriority': 50},
)


siphon_power_buff_200727 = spell(
    id=200727, name='Siphon Power', school=School.SHADOW,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_DONE, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.MOD_HEALING_DONE, misc_value=126),
    ],
    spell_icon_id=113,
    notes='warlock-rework AFFLICTION §5/§7.8: granted on a kill while draining Drain Soul (Warlock talent 1101, no XP/honor gate, §11 Q18).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Spell power increased by 10%.', 'CastingTimeIndex': 1, 'DefenseType': 0, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When a target dies while you are draining its soul, you gain 10% increased spell power for 15 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 0, 'ProcChance': 101, 'SpellClassSet': 5, 'SpellPriority': 50},
)
scripted_by(improved_life_tap_buff_200726, 'spell_warl_spell_power_pct_buff')
scripted_by(siphon_power_buff_200727, 'spell_warl_spell_power_pct_buff')


# ---------------------------------------------------------------------------
# warlock-rework AFFLICTION pass - Agonizing Pain bolt (§5/§6 (4,2)).
# ---------------------------------------------------------------------------

agonizing_pain_bolt_200728 = spell(
    id=200728, name='Agonizing Pain', school=School.SHADOW,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=29, points_per_level=2.0, implicit_target_a=6)],
    spell_icon_id=1939,
    notes='warlock-rework AFFLICTION §5/§6 (4,2): anchored at "30 at level 30, +2/level" -> 90@60, 130@80; fires when Bane of Agony crits while already at max stacks (spell_warl_agonizing_pain).',
    raw_overrides={'AttributesEx3': 65536, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Agonizing Pain.', 'EffectBonusMultiplier_1': 0.05, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_3': m.AGONIZING_PAIN, 'SpellClassSet': 5, 'SpellLevel': 30, 'BaseLevel': 30, 'SpellVisualID_1': 8339},
)
scripted_by(agonizing_pain_bolt_200728, 'spell_warl_agonizing_pain')


# ---------------------------------------------------------------------------
# warlock-rework AFFLICTION pass - Phantom Singularity damage/heal (§5/§6
# (4,1)). The castable debuff (200729) is in warlock_spells.py.
# ---------------------------------------------------------------------------

phantom_singularity_damage_200730 = spell(
    id=200730, name='Phantom Singularity', school=School.SHADOW,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0, radius_yards=10.0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=19, points_per_level=1.35, implicit_target_a=53, implicit_target_b=16, radius_yards=10.0)],
    spell_icon_id=173,
    notes='warlock-rework AFFLICTION §5/§7.17: anchored at "20/tick at level 30, +1.35/level" -> 60@60, 87@80; NOT SUPPRESS_CASTER_PROCS (must feed Shadow Pacts Tainted Soul proc, §7.15); each tick is a fresh cast (live SP/crit, not snapshotted).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Phantom Singularity damage.', 'EffectBonusMultiplier_1': 0.15, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_3': m.PHANTOM_SINGULARITY, 'SpellClassSet': 5, 'SpellLevel': 30, 'BaseLevel': 30, 'SpellVisualID_1': 8339},
)
scripted_by(phantom_singularity_damage_200730, 'spell_warl_phantom_singularity_damage')


phantom_singularity_heal_200731 = spell(
    id=200731, name='Phantom Singularity', school=School.SHADOW,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF,
    effects=[Effect(type=EffectType.HEAL, base_points=0, implicit_target_a=1)],
    spell_icon_id=173,
    notes='warlock-rework AFFLICTION §5/§7.17: BP0 = 20% of the sum of the tick damage dealt this cast (script-computed); cannot crit.',
    raw_overrides={'AttributesEx2': 536870912, 'AttributesEx3': 65536, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 0, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Phantom Singularity heal.', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 0, 'ProcChance': 101, 'SpellClassSet': 5, 'SpellPriority': 50},
)


# ---------------------------------------------------------------------------
# warlock-rework AFFLICTION pass - Soul Swap copied marker (§5/§7.9). The two
# castable Soul Swap spells (200733/200734) are in warlock_spells.py.
# ---------------------------------------------------------------------------

soul_swap_copied_200735 = spell(
    id=200735, name='Soul Swap', school=School.SHADOW,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=10000,
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY)],
    spell_icon_id=2038,
    notes='warlock-rework AFFLICTION §5/§7.9: marks that Soul Swap has a copy ready; Soul Swap: Exhale (200734) requires this via CasterAuraSpell.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage over time effects copied. Cast Soul Swap: Exhale on another target.', 'CastingTimeIndex': 1, 'DefenseType': 0, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Soul Swap.', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 0, 'ProcChance': 101, 'SpellClassSet': 5, 'SpellPriority': 50},
)


# ---------------------------------------------------------------------------
# warlock-rework AFFLICTION pass - the 11 brand-new talents' rank spells
# (§5/§6). All hidden (attributes=464, PASSIVE|DO_NOT_DISPLAY), duration -1,
# same boilerplate as every other talent-rank spell already in this file.
# ---------------------------------------------------------------------------

# --- Shadow Pact (5,0), talent 60071 - crit clause via linked_spell to the shared 200698-200700 ---
shadow_pact_200739 = spell(
    id=200739, name='Shadow Pact', school=School.NORMAL, attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY)],
    spell_icon_id=154,
    notes='warlock-rework AFFLICTION §6 (5,0): rank must stay an aura (not effect-type DUMMY) so linked_spell(type=2) to the hidden crit passive fires (§0.4 item 1).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spell critical strikes now deal 165% damage. This does not stack with other similar effects.\n\n|cFF9D9D9DCapstone Bonus: Tainted Soul. Your periodic damage critical strikes apply Tainted Soul to the target. Corruption applies 1 stack, Bane of Agony and Unstable Affliction apply 2. At 10 stacks, or when the target dies, Tainted Soul erupts for Shadow damage to the target and up to 5 enemies within 6 yards.|r', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
shadow_pact_200740 = spell(
    id=200740, name='Shadow Pact', school=School.NORMAL, attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY)],
    spell_icon_id=154,
    notes='warlock-rework AFFLICTION §6 (5,0)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spell critical strikes now deal 180% damage. This does not stack with other similar effects.\n\n|cFF9D9D9DCapstone Bonus: Tainted Soul. Your periodic damage critical strikes apply Tainted Soul to the target. Corruption applies 1 stack, Bane of Agony and Unstable Affliction apply 2. At 10 stacks, or when the target dies, Tainted Soul erupts for Shadow damage to the target and up to 5 enemies within 6 yards.|r', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
shadow_pact_200741 = spell(
    id=200741, name='Shadow Pact', school=School.NORMAL, attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY)],
    spell_icon_id=154,
    notes='warlock-rework AFFLICTION §6 (5,0) capstone: rank 3 carries the Tainted Soul proc (procs_on below).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spell critical strikes now deal 200% damage. This does not stack with other similar effects.\n\nCapstone Bonus: Tainted Soul. Your periodic damage critical strikes apply Tainted Soul to the target. Corruption applies 1 stack, Bane of Agony and Unstable Affliction apply 2. At 10 stacks, or when the target dies, Tainted Soul erupts for Shadow damage to the target and up to 5 enemies within 6 yards.', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
linked_spell(shadow_pact_200739.id, 200698, type=2)
linked_spell(shadow_pact_200740.id, 200699, type=2)
linked_spell(shadow_pact_200741.id, 200700, type=2)
scripted_by(shadow_pact_200741, 'spell_warl_shadow_pact_tainted_soul')
procs_on(shadow_pact_200741, proc_flags=0x50000, family_name=5, family_mask=m.AFFLICTION_DOTS, hit_mask=m.PROC_HIT_CRITICAL, attributes_mask=m.PROC_ATTR_TRIGGERED_CAN_PROC, spell_phase_mask=m.PROC_SPELL_PHASE_HIT, chance=100, cooldown_ms=0)


# --- Death's Grasp (0,1), talent 1005 (repurposed Suppression) ---
deaths_grasp_200742 = spell(
    id=200742, name="Death's Grasp", school=School.NORMAL, attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0,
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.MOD_CASTING_SPEED_NOT_STACK)],
    spell_icon_id=3139,
    notes='warlock-rework AFFLICTION §6 (0,1): repurposed Suppression cell (18174-176 orphaned, left declared).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell haste by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
deaths_grasp_200743 = spell(
    id=200743, name="Death's Grasp", school=School.NORMAL, attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0,
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_CASTING_SPEED_NOT_STACK)],
    spell_icon_id=3139,
    notes='warlock-rework AFFLICTION §6 (0,1)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell haste by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
deaths_grasp_200744 = spell(
    id=200744, name="Death's Grasp", school=School.NORMAL, attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0,
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MOD_CASTING_SPEED_NOT_STACK)],
    spell_icon_id=3139,
    notes='warlock-rework AFFLICTION §6 (0,1)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell haste by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


# --- Harvester of Death (0,3), talent 1668 (repurposed Improved Howl of Terror) ---
harvester_of_death_200745 = spell(
    id=200745, name='Harvester of Death', school=School.NORMAL, attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0,
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=-15001, implicit_target_a=1, apply_aura=107, misc_value=11)],
    spell_icon_id=134,
    notes='warlock-rework AFFLICTION §6 (0,3): repurposed Improved Howl of Terror cell (30054/57 orphaned, left declared); flat Death Coil cooldown reduction (category 633, 120s base -> 105/90/75s).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Death Coil by ${$m1/-1000} sec.\n\n|cFF9D9D9DCapstone Bonus: The damage and healing of your Death Coil is doubled when you are below 80% health. Reduces the cast time of your Fear by 0.2 sec, and the cast time and global cooldown of your Howl of Terror by 0.6 sec. Increases the damage your Howl of Terror victims can take before the effect breaks by 50%.|r', 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': m.DEATH_COIL, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
harvester_of_death_200746 = spell(
    id=200746, name='Harvester of Death', school=School.NORMAL, attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0,
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=-30001, implicit_target_a=1, apply_aura=107, misc_value=11)],
    spell_icon_id=134,
    notes='warlock-rework AFFLICTION §6 (0,3)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Death Coil by ${$m1/-1000} sec.\n\n|cFF9D9D9DCapstone Bonus: The damage and healing of your Death Coil is doubled when you are below 80% health. Reduces the cast time of your Fear by 0.2 sec, and the cast time and global cooldown of your Howl of Terror by 0.6 sec. Increases the damage your Howl of Terror victims can take before the effect breaks by 50%.|r', 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': m.DEATH_COIL, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
harvester_of_death_200747 = spell(
    id=200747, name='Harvester of Death', school=School.NORMAL, attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-45001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=-601, implicit_target_a=1, apply_aura=107, misc_value=10),
    ],
    spell_icon_id=134,
    notes='warlock-rework AFFLICTION §6 (0,3) capstone: eff2 flat -0.6s Howl of Terror cast time (floored at 1.0s GCD, §0.2 item 10); the rest of the capstone (Death Coil x2 below 80% health, +50% Howl break threshold) is the linked hidden passive 200748.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Death Coil by ${$m1/-1000} sec.\n\nCapstone Bonus: The damage and healing of your Death Coil is doubled when you are below 80% health. Reduces the cast time of your Fear by 0.2 sec, and the cast time and global cooldown of your Howl of Terror by 0.6 sec. Increases the damage your Howl of Terror victims can take before the effect breaks by 50%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': m.DEATH_COIL, 'EffectSpellClassMaskB_2': m.HOWL_OF_TERROR, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
linked_spell(harvester_of_death_200747.id, 200748, type=2)


harvester_of_death_capstone_200748 = spell(
    id=200748, name='Harvester of Death', school=School.SHADOW, attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-201, implicit_target_a=1, apply_aura=107, misc_value=10),
        Effect(type=EffectType.APPLY_AURA, base_points=-601, implicit_target_a=1, apply_aura=107, misc_value=21),
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=AuraType.OVERRIDE_CLASS_SCRIPTS, misc_value=7801),
    ],
    spell_icon_id=134,
    notes='warlock-rework AFFLICTION §5/§6 (0,3) capstone hidden passive, linked from Harvester of Death r3 (200747): eff1 -0.2s Fear cast time; eff2 -0.6s Howl of Terror global cooldown (flat, floors at the 1.0s GCD minimum); eff3 reuses the stock "Glyph of Fear" misc 7801 CC-break-threshold cap (SpellAuraEffects.cpp) at +50%.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Harvester of Death.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': m.FEAR, 'EffectSpellClassMaskB_2': m.HOWL_OF_TERROR, 'EffectSpellClassMaskC_2': m.HOWL_OF_TERROR, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


# --- Lingering Agony (2,2), talent 2205 (repurposed Improved Fear) ---
lingering_agony_200749 = spell(
    id=200749, name='Lingering Agony', school=School.NORMAL, attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0,
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=2999, implicit_target_a=1, apply_aura=107, misc_value=1)],
    spell_icon_id=1494,
    notes='warlock-rework AFFLICTION §6 (2,2): repurposed Improved Fear cell (53754/59 orphaned, left declared); +3/6 sec duration on Bane of Agony and Unstable Affliction.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the duration of your Bane of Agony and Unstable Affliction by $/1000;s1 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': m.LINGERING_AGONY[0], 'EffectSpellClassMaskA_2': m.LINGERING_AGONY[1], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
lingering_agony_200750 = spell(
    id=200750, name='Lingering Agony', school=School.NORMAL, attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0,
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=5999, implicit_target_a=1, apply_aura=107, misc_value=1)],
    spell_icon_id=1494,
    notes='warlock-rework AFFLICTION §6 (2,2)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the duration of your Bane of Agony and Unstable Affliction by $/1000;s1 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': m.LINGERING_AGONY[0], 'EffectSpellClassMaskA_2': m.LINGERING_AGONY[1], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


# --- Creeping Agony (3,2), talent 1061 (repurposed Amplify Curse) ---
creeping_agony_200751 = spell(
    id=200751, name='Creeping Agony', school=School.NORMAL, attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0,
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_CUSTOM_STAT_PCT, misc_value=1048576)],
    spell_icon_id=1468,
    notes='warlock-rework AFFLICTION §6 (3,2): repurposed Amplify Curse cell (18288 orphaned, left declared); +2/4/6% Mastery.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Mastery by $s1%.\n\n|cFF9D9D9DCapstone Bonus: When you cast Bane of Agony, it also applies to one nearby enemy in combat that does not already have Bane of Agony.|r', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
creeping_agony_200752 = spell(
    id=200752, name='Creeping Agony', school=School.NORMAL, attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0,
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.MOD_CUSTOM_STAT_PCT, misc_value=1048576)],
    spell_icon_id=1468,
    notes='warlock-rework AFFLICTION §6 (3,2)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Mastery by $s1%.\n\n|cFF9D9D9DCapstone Bonus: When you cast Bane of Agony, it also applies to one nearby enemy in combat that does not already have Bane of Agony.|r', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
creeping_agony_200753 = spell(
    id=200753, name='Creeping Agony', school=School.NORMAL, attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0,
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.MOD_CUSTOM_STAT_PCT, misc_value=1048576)],
    spell_icon_id=1468,
    notes='warlock-rework AFFLICTION §6 (3,2) capstone: rank 3 carries the Bane-of-Agony-spread clause (spell_warl_bane_of_agony AfterHit, §7.2) - data only.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Mastery by $s1%.\n\nCapstone Bonus: When you cast Bane of Agony, it also applies to one nearby enemy in combat that does not already have Bane of Agony.', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


# --- Agonizing Pain (4,2), talent 60070 (minted) ---
agonizing_pain_200754 = spell(
    id=200754, name='Agonizing Pain', school=School.NORMAL, attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=32),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1939,
    notes='warlock-rework AFFLICTION §6 (4,2): eff1 +1/2% Shadow damage (§11 Q1, user); eff2 is a plain proc carrier (no roll - both clauses fire on every crit at both ranks).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Shadow damage by $s1%.  When your Bane of Agony critically strikes, it gains an additional stack.  While your Bane of Agony is at maximum stacks, its critical ticks deal an additional $200728s1 Shadow damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
agonizing_pain_200755 = spell(
    id=200755, name='Agonizing Pain', school=School.NORMAL, attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=32),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1939,
    notes='warlock-rework AFFLICTION §6 (4,2)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Shadow damage by $s1%.  When your Bane of Agony critically strikes, it gains an additional stack.  While your Bane of Agony is at maximum stacks, its critical ticks deal an additional $200728s1 Shadow damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
scripted_by(agonizing_pain_200754, 'spell_warl_agonizing_pain')
scripted_by(agonizing_pain_200755, 'spell_warl_agonizing_pain')
procs_on(agonizing_pain_200754, proc_flags=m.PROC_FLAG_DONE_PERIODIC, family_name=5, family_mask=(m.BANE_OF_AGONY, 0, 0), hit_mask=m.PROC_HIT_CRITICAL, spell_phase_mask=m.PROC_SPELL_PHASE_HIT, chance=100, cooldown_ms=0)
procs_on(agonizing_pain_200755, proc_flags=m.PROC_FLAG_DONE_PERIODIC, family_name=5, family_mask=(m.BANE_OF_AGONY, 0, 0), hit_mask=m.PROC_HIT_CRITICAL, spell_phase_mask=m.PROC_SPELL_PHASE_HIT, chance=100, cooldown_ms=0)


# --- Fatal Echoes (6,2), talent 1022 (repurposed Dark Pact) ---
fatal_echoes_200756 = spell(
    id=200756, name='Fatal Echoes', school=School.NORMAL, attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0,
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=3)],
    spell_icon_id=1933,
    notes='warlock-rework AFFLICTION §6 (6,2): repurposed Dark Pact cell (18220 orphaned, left declared); +2/4/6% Intellect.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Intellect by $s1%.\n\n|cFF9D9D9DCapstone Bonus: When your Unstable Affliction expires, it has a 15% chance to refresh itself.|r', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
fatal_echoes_200757 = spell(
    id=200757, name='Fatal Echoes', school=School.NORMAL, attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0,
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=3)],
    spell_icon_id=1933,
    notes='warlock-rework AFFLICTION §6 (6,2)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Intellect by $s1%.\n\n|cFF9D9D9DCapstone Bonus: When your Unstable Affliction expires, it has a 15% chance to refresh itself.|r', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
fatal_echoes_200758 = spell(
    id=200758, name='Fatal Echoes', school=School.NORMAL, attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0,
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=3)],
    spell_icon_id=1933,
    notes='warlock-rework AFFLICTION §6 (6,2) capstone: rank 3 carries the "Unstable Affliction has a 15% chance to refresh itself on expiry" clause (spell_warl_unstable_affliction_affliction, §7.18) - data only.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Intellect by $s1%.\n\nCapstone Bonus: When your Unstable Affliction expires, it has a 15% chance to refresh itself.', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


# --- Virulence (7,0), talent 60072 (minted) ---
virulence_200759 = spell(
    id=200759, name='Virulence', school=School.NORMAL, attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0,
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=108, misc_value=22)],
    spell_icon_id=1932,
    notes='warlock-rework AFFLICTION §6 (7,0): +2/4/6% Corruption damage.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage of your Corruption by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Your Seed of Corruption's detonation applies Corruption to every enemy it damages.|r", 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
virulence_200760 = spell(
    id=200760, name='Virulence', school=School.NORMAL, attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0,
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=108, misc_value=22)],
    spell_icon_id=1932,
    notes='warlock-rework AFFLICTION §6 (7,0)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage of your Corruption by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Your Seed of Corruption's detonation applies Corruption to every enemy it damages.|r", 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
virulence_200761 = spell(
    id=200761, name='Virulence', school=School.NORMAL, attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0,
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=108, misc_value=22)],
    spell_icon_id=1932,
    notes='warlock-rework AFFLICTION §6 (7,0) capstone: rank 3 carries the "Seed detonation applies Corruption" clause (Warlock::AddAura in the detonation AfterHit, §7.6) - data only.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage of your Corruption by $s1%.\n\nCapstone Bonus: Your Seed of Corruption's detonation applies Corruption to every enemy it damages.", 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


# --- Compounding Darkness (7,2), talent 60073 (minted) ---
compounding_darkness_200762 = spell(
    id=200762, name='Compounding Darkness', school=School.NORMAL, attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0,
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.DUMMY)],
    spell_icon_id=2901,
    notes='warlock-rework AFFLICTION §6 (7,2): +3/6/9% Unstable Affliction damage per other Affliction DoT on the target (read by spell_warl_unstable_affliction_affliction).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Unstable Affliction deals $s1% increased damage for each of your other Affliction damage over time effects on the target.', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
compounding_darkness_200763 = spell(
    id=200763, name='Compounding Darkness', school=School.NORMAL, attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0,
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.DUMMY)],
    spell_icon_id=2901,
    notes='warlock-rework AFFLICTION §6 (7,2)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Unstable Affliction deals $s1% increased damage for each of your other Affliction damage over time effects on the target.', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
compounding_darkness_200764 = spell(
    id=200764, name='Compounding Darkness', school=School.NORMAL, attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0,
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=AuraType.DUMMY)],
    spell_icon_id=2901,
    notes='warlock-rework AFFLICTION §6 (7,2)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Unstable Affliction deals $s1% increased damage for each of your other Affliction damage over time effects on the target.', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


# --- Inevitable Demise capstone hidden passive (§5/§6 (1,3)), linked from Siphon Power r2 (18372) ---
inevitable_demise_capstone_200769 = spell(
    id=200769, name='Inevitable Demise', school=School.SHADOW, attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200723)],
    spell_icon_id=153,
    notes='warlock-rework AFFLICTION §5/§6 (1,3): hidden passive, linked from Siphon Power r2 (18372); procs (below) grant a stack of Inevitable Demise (200723) on every Bane of Agony tick.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Inevitable Demise.', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
procs_on(inevitable_demise_capstone_200769, proc_flags=m.PROC_FLAG_DONE_PERIODIC, family_name=5, family_mask=(m.BANE_OF_AGONY, 0, 0), spell_type_mask=1, spell_phase_mask=m.PROC_SPELL_PHASE_HIT, chance=100, cooldown_ms=0)


# --- Fel Concentration r3 capstone heal (§5/§6 (2,1)) ---
fel_concentration_heal_200770 = spell(
    id=200770, name='Fel Concentration', school=School.SHADOW,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF,
    effects=[Effect(type=EffectType.HEAL, base_points=0, implicit_target_a=1)],
    spell_icon_id=76,
    notes='warlock-rework AFFLICTION §5/§7.19: BP0 = min(20% of the periodic damage dealt this tick, 5% max health) - only while the leech talent gate (Warlock::LeechTalent::FelConcentration) is active; cannot crit.',
    raw_overrides={'AttributesEx2': 536870912, 'AttributesEx3': 65536, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 0, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Fel Concentration heal.', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 0, 'ProcChance': 101, 'SpellClassSet': 5, 'SpellPriority': 50},
)
scripted_by(fel_concentration_heal_200770, 'spell_warl_fel_concentration_capstone')


# --- Improved Felhunter pet damage buff (§5/§6 (5,3)) ---
improved_felhunter_pet_buff_200771 = spell(
    id=200771, name='Improved Felhunter', school=School.SHADOW, attributes=128,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=5, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=127)],
    spell_icon_id=2027,
    notes='warlock-rework AFFLICTION §5/§6 (5,3): kept on the Felhunter by spell_warl_improved_felhunter (CastCustomSpell with BP0 = the ranks live 10/20%); hidden (attributes 0x80).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Felhunter damage increased by $s1%.', 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Improved Felhunter.', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 5, 'SpellPriority': 50},
)


# ---------------------------------------------------------------------------
# warlock-rework AFFLICTION pass - talent row 1226 (Demonology tab (2,2))
# repurposed IN PLACE as Impending Doom, per PLAN §11 Q7 / DEMONOLOGY.md §6
# (user 2026-09-27): "S1 writes the row with ranks 200869/200870 (data
# only); S3 adds spell_warl_impending_doom, the 200870 proc row and the
# rest of §6's data, and must not re-create or move it." B13 (this pass)
# already stops 1226 granting Fel Domination (now baseline, warlock_spells.py).
# Exact data per DEMONOLOGY.md §6 (2,2): eff1 ADD_PCT_MODIFIER DOT stored
# 9/19 (10/20%) masked to Demonology's still-unminted Bane of Doom bit
# (d3 bit 23, _masks.py's DEMONOLOGY_D3_BIT_23 placeholder); r2 adds a DUMMY
# capstone marker (its proc is S3's, not built here).
# ---------------------------------------------------------------------------

impending_doom_200869 = spell(
    id=200869, name='Impending Doom', school=School.NORMAL, attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0,
    effects=[Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=22)],
    spell_icon_id=170,
    notes='warlock-rework AFFLICTION §11 Q7 (Demonology tab (2,2), talent 1226 repurposed in place): data only per DEMONOLOGY.md §6 - S3 (Demonology pass) adds the script/proc and completes the tooltip capstone text. Placeholder tooltip until then.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Bane of Doom by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_3': m.DEMONOLOGY_D3_BIT_23, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
impending_doom_200870 = spell(
    id=200870, name='Impending Doom', school=School.NORMAL, attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=170,
    notes='warlock-rework AFFLICTION §11 Q7: rank 2 capstone marker (eff2 DUMMY) - S3 binds the "critical strikes from Bane of Doom summon a Wild Imp" proc to this id.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Bane of Doom by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_3': m.DEMONOLOGY_D3_BIT_23, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


# ---------------------------------------------------------------------------
# warlock-rework DESTRUCTION pass (S2), WP-0 §3 items 1-2:
# - pulled DSL rows for stock spells this pass retunes/rebinds (pull_dsl.py
#   34936 47283 54274 54276 54277 54370 54371 54372 54373 54374 54375 47960
#   18118 --constants); their source/spells/npc.csv rows were deleted in the
#   same change.
# - Backlash 34935/34938/34939 moved here from mage/mage_trigger_spells.py
#   and Molten Skin 63349/63350/63351 from rogue/rogue_trigger_spells.py
#   (both are Warlock talents that were left filed under their old stock
#   SpellFamily's DSL file); SpellClassSet corrected 3/8 -> 5 (Warlock).
#   warlock_talents.py's granted_by_talent() rows 1817/1887 already grant
#   these ranks by bare int - switched to reference the objects below.
# ---------------------------------------------------------------------------

backlash_34936 = spell(
    id=34936,
    name='Backlash',
    school=School.FIRE,
    dispel=DispelType.MAGIC,
    attributes=262144,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=10),
    ],
    spell_icon_id=2130,
    notes='warlock-rework DESTRUCTION §5 (Backlash 4,0 proc buff): duration_ms 8000 -> 20000; mask scoped to Immolate only (A_1 = IMMOLATE 0x4, A_2 cleared - was Shadow Bolt|Incinerate). ProcCharges 1 (also set at load, SpellInfoCorrections.cpp:260). Consumed only by an Immolate the warlock casts (spell_warl_backlash-equivalent consumption is the engine\'s own SpellMod charge spend on Immolate cast - Fury of the Void\'s AddAura(348) does not consume it, G13/§7.13).',
    raw_overrides={'AttributesEx': 32768, 'AttributesEx3': 262144, 'AttributesEx4': 64, 'AttributesEx6': 64, 'CastingTimeIndex': 1, 'ProcChance': 101, 'SpellLevel': 1, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': m.IMMOLATE, 'EffectSpellClassMaskA_2': 0, 'SpellVisualID_1': 8259, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'Increases your critical strike chance with all spells and abilities and gives you a chance for your Immolate periodic damage to make your next Immolate instant.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next Immolate is instant.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 5, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)
procs_on(34936, proc_flags=m.PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG, family_name=5, family_mask=(m.IMMOLATE, 0, 0), spell_phase_mask=m.PROC_SPELL_PHASE_CAST, attributes_mask=m.PROC_ATTR_REQ_SPELLMOD, charges=1)


empowered_imp_47283 = spell(
    id=47283,
    name='Empowered Imp',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    attributes=168099840,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=27, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=7),
    ],
    spell_icon_id=3171,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'CastingTimeIndex': 1, 'ProcTypeMask': 69632, 'ProcChance': 100, 'ProcCharges': 1, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 933, 'EffectSpellClassMaskA_2': 8622272, 'SpellVisualID_1': 7424, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'Critical effect chance of next spell increased by $s1%.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Critical effect chance of next spell increased by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 5, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_2': 1.0},
)


backdraft_54274 = spell(
    id=54274,
    name='Backdraft',
    school=School.NORMAL,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=10),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=21),
    ],
    spell_icon_id=3170,
    notes='pulled from existing data',
    raw_overrides={'CastingTimeIndex': 1, 'ProcTypeMask': 86016, 'ProcChance': 100, 'ProcCharges': 3, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 293, 'EffectSpellClassMaskA_2': 200896, 'EffectSpellClassMaskB_1': 293, 'EffectSpellClassMaskB_2': 200896, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'Cast time and global cooldown of your next three Destruction spell reduced by $s1%.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Reduced cast time and global cooldown for your Destruction spells by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 5, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


backdraft_54276 = spell(
    id=54276,
    name='Backdraft',
    school=School.NORMAL,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=10),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=21),
    ],
    spell_icon_id=3170,
    notes='pulled from existing data',
    raw_overrides={'CastingTimeIndex': 1, 'ProcTypeMask': 86016, 'ProcChance': 100, 'ProcCharges': 3, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 357, 'EffectSpellClassMaskA_2': 200896, 'EffectSpellClassMaskB_1': 357, 'EffectSpellClassMaskB_2': 200896, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'Cast time and global cooldown of your next three Destruction spell reduced by $s1%.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Reduced cast time and global cooldown for your Destruction spells by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 5, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


backdraft_54277 = spell(
    id=54277,
    name='Backdraft',
    school=School.NORMAL,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=10),
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=21),
    ],
    spell_icon_id=3170,
    notes='pulled from existing data',
    raw_overrides={'CastingTimeIndex': 1, 'ProcTypeMask': 86016, 'ProcChance': 100, 'ProcCharges': 3, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 357, 'EffectSpellClassMaskA_2': 200896, 'EffectSpellClassMaskB_1': 357, 'EffectSpellClassMaskB_2': 200896, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'Cast time and global cooldown of your next three Destruction spell reduced by $s1%.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Reduced cast time and global cooldown for your Destruction spells by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 5, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


nether_protection_54370 = spell(
    id=54370,
    name='Nether Protection',
    school=School.NORMAL,
    dispel=DispelType.MAGIC,
    attributes=151257088,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=2),
    ],
    spell_icon_id=1985,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 268435456, 'AttributesEx4': 16512, 'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 997, 'SpellVisualID_1': 9750, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'After being hit with a spell, you have a chance to gain Nether Protection, reducing all damage by that spell school by $s1% for $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Holy spell damage reduced by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 5, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


nether_protection_54371 = spell(
    id=54371,
    name='Nether Protection',
    school=School.NORMAL,
    dispel=DispelType.MAGIC,
    attributes=151257088,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=4),
    ],
    spell_icon_id=1985,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 268435456, 'AttributesEx4': 16512, 'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 997, 'SpellVisualID_1': 9750, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'After being hit with a spell, you have a chance to gain Nether Protection, reducing all damage by that spell school by $s1% for $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Fire spell damage reduced by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 5, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


nether_protection_54372 = spell(
    id=54372,
    name='Nether Protection',
    school=School.NORMAL,
    dispel=DispelType.MAGIC,
    attributes=151257088,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=16),
    ],
    spell_icon_id=1985,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 268435456, 'AttributesEx4': 16512, 'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 997, 'SpellVisualID_1': 9750, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'After being hit with a spell, you have a chance to gain Nether Protection, reducing all damage by that spell school by $s1% for $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Frost spell damage reduced by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 5, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


nether_protection_54373 = spell(
    id=54373,
    name='Nether Protection',
    school=School.NORMAL,
    dispel=DispelType.MAGIC,
    attributes=151257088,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=64),
    ],
    spell_icon_id=1985,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 268435456, 'AttributesEx4': 16512, 'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 997, 'SpellVisualID_1': 9750, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'After being hit with a spell, you have a chance to gain Nether Protection, reducing all damage by that spell school by $s1% for $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Arcane spell damage reduced by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 5, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


nether_protection_54374 = spell(
    id=54374,
    name='Nether Protection',
    school=School.NORMAL,
    dispel=DispelType.MAGIC,
    attributes=151257088,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=32),
    ],
    spell_icon_id=1985,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 268435456, 'AttributesEx4': 16512, 'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 997, 'SpellVisualID_1': 9750, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'After being hit with a spell, you have a chance to gain Nether Protection, reducing all damage by that spell school by $s1% for $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Shadow spell damage reduced by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 5, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


nether_protection_54375 = spell(
    id=54375,
    name='Nether Protection',
    school=School.NORMAL,
    dispel=DispelType.MAGIC,
    attributes=151257088,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=8),
    ],
    spell_icon_id=1985,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 268435456, 'AttributesEx4': 16512, 'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 997, 'SpellVisualID_1': 9750, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'After being hit with a spell, you have a chance to gain Nether Protection, reducing all damage by that spell school by $s1% for $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Nature spell damage reduced by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 5, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


shadowflame_47960 = spell(
    id=47960,
    name='Shadowflame',
    school=School.FIRE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=113, points_per_level=2.266667, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=2000),
    ],
    spell_icon_id=3317,
    notes='warlock-rework DESTRUCTION §4.1 (B3 rebase, matches 47897s learn level 75->50): bp/ppl rescaled so the level-60 value is unchanged (114 @50, 136 @60, 182 @80, +34% vs todays @80); MaxLevel 83->80 (matches the class-wide 80 cap); coefficient (spell_bonus_data dot 0.0667) unchanged/undeclared - its row survives live (only 47897s own row was deleted by 2026_09_01_26.sql).',
    raw_overrides={'AttributesEx2': 4, 'AttributesEx3': 262144, 'CastingTimeIndex': 1, 'InterruptFlags': 15, 'ProcChance': 101, 'MaxLevel': 80, 'BaseLevel': 50, 'SpellLevel': 50, 'EquippedItemClass': -1, 'EffectDieSides_2': 1, 'EffectBasePoints_2': -1, 'ImplicitTargetA_3': 6, 'SpellVisualID_1': 11247, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'Targets in a cone in front of the caster take $47897s1 Shadow damage and an additional $47960o1 Fire damage over $47960d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s1 Fire damage every $t1 seconds.', 'AuraDescription_Lang_Mask': 16712190, 'StartRecoveryTime': 1500, 'SpellClassSet': 5, 'SpellClassMask_3': 2, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_2': 0.10700000077486038},
)


aftermath_18118 = spell(
    id=18118,
    name='Aftermath',
    school=School.FIRE,
    dispel=DispelType.MAGIC,
    mechanic=27,
    attributes=8388608,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-71, mechanic=Mechanic.SNARE, implicit_target_a=6, apply_aura=AuraType.MOD_DECREASE_SPEED),
    ],
    spell_icon_id=11,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 136, 'AttributesEx2': 4, 'AttributesEx3': 131072, 'CastingTimeIndex': 1, 'ProcChance': 101, 'EquippedItemClass': -1, 'SpellVisualID_1': 84, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Increases the periodic damage done by your Immolate, and your Conflagrate has a chance to daze the target for $18118d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Dazed.', 'AuraDescription_Lang_Mask': 16712190, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


backlash_34935 = spell(
    id=34935,
    name='Backlash',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=34936),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_PCT),
    ],
    spell_icon_id=2130,
    notes='warlock-rework DESTRUCTION §6 (4,0): eff0 junk mask 0x400015 -> IMMOLATE (0x4); eff1 aura 57 -> 290 MOD_CRIT_PCT (bp unchanged, 1/2/3%). ProcChance 8/16/25 -> 3/6/10, ProcTypeMask 680 -> DONE_PERIODIC (0x40000) - row §8 -34935.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your critical strike chance with all spells and abilities by $s2%. Your Immolate periodic damage has a $h% chance to make your next Immolate instant. Lasts $34936d. Cannot occur more than once every 8 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.IMMOLATE, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 3, 'ProcTypeMask': m.PROC_FLAG_DONE_PERIODIC, 'RangeIndex': 1, 'SpellClassSet': 5, 'SpellLevel': 1, 'SpellPriority': 50},
)


backlash_34938 = spell(
    id=34938,
    name='Backlash',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=34936),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_PCT),
    ],
    spell_icon_id=2130,
    notes='warlock-rework DESTRUCTION §6 (4,0): see rank 1s note.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your critical strike chance with all spells and abilities by $s2%. Your Immolate periodic damage has a $h% chance to make your next Immolate instant. Lasts $34936d. Cannot occur more than once every 8 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.IMMOLATE, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 6, 'ProcTypeMask': m.PROC_FLAG_DONE_PERIODIC, 'RangeIndex': 1, 'SpellClassSet': 5, 'SpellLevel': 1, 'SpellPriority': 50},
)


backlash_34939 = spell(
    id=34939,
    name='Backlash',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=34936),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_PCT),
    ],
    spell_icon_id=2130,
    notes='warlock-rework DESTRUCTION §6 (4,0): see rank 1s note.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your critical strike chance with all spells and abilities by $s2%. Your Immolate periodic damage has a $h% chance to make your next Immolate instant. Lasts $34936d. Cannot occur more than once every 8 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.IMMOLATE, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 10, 'ProcTypeMask': m.PROC_FLAG_DONE_PERIODIC, 'RangeIndex': 1, 'SpellClassSet': 5, 'SpellLevel': 1, 'SpellPriority': 50},
)
procs_on(-34935, proc_flags=m.PROC_FLAG_DONE_PERIODIC, family_name=5, family_mask=(m.IMMOLATE, 0, 0), spell_type_mask=m.PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=m.PROC_SPELL_PHASE_HIT, chance=0, cooldown_ms=8000)


molten_skin_63349 = spell(
    id=63349,
    name='Molten Skin',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=2307,
    notes='warlock-rework DESTRUCTION §6 (1,1): eff0 rewritten from MOD_DAMAGE_PERCENT_TAKEN (all damage) to ADD_PCT_MODIFIER DOT (SPELLMOD_DOT, misc 22 - Hellfires self-damage 1949 eff1 is the only periodic-damage effect under d1 0x40; 5857 is direct) bp -3/-5/-7 -> -11/-21/-31 (-10/-20/-30%), A_1 = HELLFIRE (0x40). AttributesEx3 INSTANT_TARGET_PROCS (0x80000) cleared.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces all damage taken by your Hellfire by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Your Rain of Fire and Hellfire damage has a 2% chance per hit to reset the cooldown of Shadowfury. This effect cannot occur more than once every 15 sec.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.HELLFIRE, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5, 'SpellLevel': 1, 'SpellPriority': 50},
)


molten_skin_63350 = spell(
    id=63350,
    name='Molten Skin',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=2307,
    notes='warlock-rework DESTRUCTION §6 (1,1): see rank 1s note.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces all damage taken by your Hellfire by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Your Rain of Fire and Hellfire damage has a 2% chance per hit to reset the cooldown of Shadowfury. This effect cannot occur more than once every 15 sec.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.HELLFIRE, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5, 'SpellLevel': 1, 'SpellPriority': 50},
)


molten_skin_63351 = spell(
    id=63351,
    name='Molten Skin',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2307,
    notes='warlock-rework DESTRUCTION §6 (1,1): r3 final rank, new eff1 DUMMY (proc carrier for the Shadowfury cooldown reset capstone, §8 63351 row: fam 5 (0x60,0,0), HIT, chance 2, cooldown 15000, DONE_PERIODIC included since Hellfires self-damage procs as periodic, C33).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces all damage taken by your Hellfire by $s1%.\n\nCapstone Bonus: Your Rain of Fire and Hellfire damage has a 2% chance per hit to reset the cooldown of Shadowfury. This effect cannot occur more than once every 15 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.HELLFIRE, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5, 'SpellLevel': 1, 'SpellPriority': 50},
)
scripted_by(molten_skin_63351, 'spell_warl_molten_skin')
procs_on(molten_skin_63351, proc_flags=m.PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG | m.PROC_FLAG_DONE_PERIODIC, family_name=5, family_mask=(0x60, 0, 0), spell_type_mask=m.PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=m.PROC_SPELL_PHASE_HIT, attributes_mask=m.PROC_ATTR_TRIGGERED_CAN_PROC, chance=2, cooldown_ms=15000, disable_effects_mask=0x1)


# ---------------------------------------------------------------------------
# warlock-rework DESTRUCTION pass (S2) - new spells (§5, DESTRUCTION.md §2.1).
# Talent-rank passives (Volatility, Kindling, Hellstorm, Fury of the Void,
# Chaotic Resonance) plus every triggered/buff/debuff spell the tree needs.
# Talent grants (granted_by_talent, SLA rows) live in warlock_talents.py.
# ---------------------------------------------------------------------------

volatility_200960 = spell(
    id=200960,
    name='Volatility',
    school=School.NORMAL,
    attributes=464,
    duration_ms=-1,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_CUSTOM_STAT_PCT, misc_value=1 << 11),
    ],
    spell_icon_id=2340,
    notes='warlock-rework DESTRUCTION §6 (0,0) NEW talent 965 (repurposed from Improved Searing Pain): misc = 1 << CombatRating.PROC_CHANCE (2048).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Proc Chance increased by $s1%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Proc Chance by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


volatility_200961 = spell(
    id=200961,
    name='Volatility',
    school=School.NORMAL,
    attributes=464,
    duration_ms=-1,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.MOD_CUSTOM_STAT_PCT, misc_value=1 << 11),
    ],
    spell_icon_id=2340,
    notes='warlock-rework DESTRUCTION §6 (0,0): r2, see r1s note.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Proc Chance increased by $s1%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Proc Chance by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


volatility_200962 = spell(
    id=200962,
    name='Volatility',
    school=School.NORMAL,
    attributes=464,
    duration_ms=-1,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.MOD_CUSTOM_STAT_PCT, misc_value=1 << 11),
    ],
    spell_icon_id=2340,
    notes='warlock-rework DESTRUCTION §6 (0,0): r3 final rank, see r1s note.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Proc Chance increased by $s1%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Proc Chance by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


kindling_200963 = spell(
    id=200963,
    name='Kindling',
    school=School.NORMAL,
    attributes=464,
    duration_ms=-1,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=999, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=2298,
    notes='warlock-rework DESTRUCTION §6 (0,3) NEW talent 60100: ADD_FLAT_MODIFIER DURATION (+1/2/3s), A_1 = IMMOLATE (0x4).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Immolate duration increased by $/1000;s1 sec.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the duration of your Immolate by $/1000;s1 sec.\n\n|cFF9D9D9DCapstone Bonus: Your Shadow Bolt and Incinerate casts have a 10% chance to fire 4 Molten Bolts at the target, one every 0.5 sec, each dealing $200985s1 Fire damage.|r', 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': m.IMMOLATE, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


kindling_200964 = spell(
    id=200964,
    name='Kindling',
    school=School.NORMAL,
    attributes=464,
    duration_ms=-1,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1999, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=2298,
    notes='warlock-rework DESTRUCTION §6 (0,3): r2, see r1s note.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Immolate duration increased by $/1000;s1 sec.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the duration of your Immolate by $/1000;s1 sec.\n\n|cFF9D9D9DCapstone Bonus: Your Shadow Bolt and Incinerate casts have a 10% chance to fire 4 Molten Bolts at the target, one every 0.5 sec, each dealing $200985s1 Fire damage.|r', 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': m.IMMOLATE, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


kindling_200965 = spell(
    id=200965,
    name='Kindling',
    school=School.NORMAL,
    attributes=464,
    duration_ms=-1,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2999, implicit_target_a=1, apply_aura=107, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200984),
    ],
    spell_icon_id=2298,
    notes='warlock-rework DESTRUCTION §6 (0,3): r3 final rank, new eff1 PROC_TRIGGER_SPELL -> 200984 Molten Bolts (§8: fam 5 (0x1, 0x40, 0), HIT, chance 10, disable 0x1).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Immolate duration increased by $/1000;s1 sec.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the duration of your Immolate by $/1000;s1 sec.\n\nCapstone Bonus: Your Shadow Bolt and Incinerate casts have a 10% chance to fire 4 Molten Bolts at the target, one every 0.5 sec, each dealing $200985s1 Fire damage.', 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': m.IMMOLATE, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
procs_on(kindling_200965, proc_flags=m.PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG, family_name=5, family_mask=(m.SHADOW_BOLT, m.INCINERATE, 0), spell_type_mask=m.PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=m.PROC_SPELL_PHASE_HIT, chance=10, cooldown_ms=0, disable_effects_mask=0x1)


hellstorm_200966 = spell(
    id=200966,
    name='Hellstorm',
    school=School.NORMAL,
    attributes=464,
    duration_ms=-1,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=2385,
    notes='warlock-rework DESTRUCTION §6 (2,2) NEW talent 60101: eff0 ADD_PCT_MODIFIER DAMAGE (+5/10/15%), A_1 = 0xA0 (RoF | Shadowburn). eff1 ADD_PCT_MODIFIER COST (-10/-20/-30%), B_1 = 0xA0.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Rain of Fire and Shadowburn damage increased by $s1%, mana cost reduced by $s2%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Rain of Fire and Shadowburn by $s1% and reduces their mana cost by $s2%.\n\n|cFF9D9D9DCapstone Bonus: Your Rain of Fire damage has a 3% chance per hit to make your Hellfire tick 50% faster for 8 sec. While active, each Hellfire tick deals 33% less damage to you, so your damage taken per second is unchanged.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': m.RAIN_OF_FIRE | m.SHADOWBURN, 'EffectSpellClassMaskB_1': m.RAIN_OF_FIRE | m.SHADOWBURN, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


hellstorm_200967 = spell(
    id=200967,
    name='Hellstorm',
    school=School.NORMAL,
    attributes=464,
    duration_ms=-1,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=2385,
    notes='warlock-rework DESTRUCTION §6 (2,2): r2, see r1s note.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Rain of Fire and Shadowburn damage increased by $s1%, mana cost reduced by $s2%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Rain of Fire and Shadowburn by $s1% and reduces their mana cost by $s2%.\n\n|cFF9D9D9DCapstone Bonus: Your Rain of Fire damage has a 3% chance per hit to make your Hellfire tick 50% faster for 8 sec. While active, each Hellfire tick deals 33% less damage to you, so your damage taken per second is unchanged.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': m.RAIN_OF_FIRE | m.SHADOWBURN, 'EffectSpellClassMaskB_1': m.RAIN_OF_FIRE | m.SHADOWBURN, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


hellstorm_200968 = spell(
    id=200968,
    name='Hellstorm',
    school=School.NORMAL,
    attributes=464,
    duration_ms=-1,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=108, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL),
    ],
    spell_icon_id=2385,
    notes='warlock-rework DESTRUCTION §6 (2,2): r3 final rank, new eff2 PROC_TRIGGER_SPELL carrier for the Hellstorm-buff capstone (§8: fam 5 (0x20,0,0), HIT, attr TRIGGERED_CAN_PROC, chance 3, cooldown 10000, disable 0x3); spell_warl_hellstorm_proc (WP-B) CheckProc excludes overlap with 200989.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Rain of Fire and Shadowburn damage increased by $s1%, mana cost reduced by $s2%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Rain of Fire and Shadowburn by $s1% and reduces their mana cost by $s2%.\n\nCapstone Bonus: Your Rain of Fire damage has a 3% chance per hit to make your Hellfire tick 50% faster for 8 sec. While active, each Hellfire tick deals 33% less damage to you, so your damage taken per second is unchanged.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': m.RAIN_OF_FIRE | m.SHADOWBURN, 'EffectSpellClassMaskB_1': m.RAIN_OF_FIRE | m.SHADOWBURN, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
scripted_by(hellstorm_200968, 'spell_warl_hellstorm_proc')
procs_on(hellstorm_200968, proc_flags=m.PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG, family_name=5, family_mask=(m.RAIN_OF_FIRE, 0, 0), spell_type_mask=m.PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=m.PROC_SPELL_PHASE_HIT, attributes_mask=m.PROC_ATTR_TRIGGERED_CAN_PROC, chance=3, cooldown_ms=10000, disable_effects_mask=0x3)


fury_of_the_void_200971 = spell(
    id=200971,
    name='Fury of the Void',
    school=School.NORMAL,
    attributes=464,
    duration_ms=-1,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=199, implicit_target_a=1, apply_aura=107, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=2356,
    notes='warlock-rework DESTRUCTION §6 (7,0) NEW talent 1889 (repurposed from Improved Soul Leech): eff0 ADD_FLAT_MODIFIER DURATION (+0.2/0.4/0.6s), A_2 = SHADOWFURY (0x1000). eff1 ADD_PCT_MODIFIER DAMAGE (+10/20/30%), B_2 = SHADOWFURY|SHADOWFLAME (0x11000). eff2 ADD_PCT_MODIFIER DOT (+10/20/30%), C_3 = SHADOWFLAME_DOT (0x2).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Shadowfury duration increased, Shadowfury/Shadowflame damage increased.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the duration of Shadowfury by $/1000;s1 seconds and increases the damage of your Shadowfury and Shadowflame by $s2%.\n\n|cFF9D9D9DCapstone Bonus: Your Shadowfury also afflicts all enemies hit with the periodic effect of your Immolate.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': m.SHADOWFURY, 'EffectSpellClassMaskB_2': m.SHADOWFURY | m.SHADOWFLAME, 'EffectSpellClassMaskC_3': m.SHADOWFLAME_DOT, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


fury_of_the_void_200972 = spell(
    id=200972,
    name='Fury of the Void',
    school=School.NORMAL,
    attributes=464,
    duration_ms=-1,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=399, implicit_target_a=1, apply_aura=107, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=2356,
    notes='warlock-rework DESTRUCTION §6 (7,0): r2, see r1s note.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Shadowfury duration increased, Shadowfury/Shadowflame damage increased.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the duration of Shadowfury by $/1000;s1 seconds and increases the damage of your Shadowfury and Shadowflame by $s2%.\n\n|cFF9D9D9DCapstone Bonus: Your Shadowfury also afflicts all enemies hit with the periodic effect of your Immolate.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': m.SHADOWFURY, 'EffectSpellClassMaskB_2': m.SHADOWFURY | m.SHADOWFLAME, 'EffectSpellClassMaskC_3': m.SHADOWFLAME_DOT, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


fury_of_the_void_200973 = spell(
    id=200973,
    name='Fury of the Void',
    school=School.NORMAL,
    attributes=464,
    duration_ms=-1,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=599, implicit_target_a=1, apply_aura=107, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=2356,
    notes='warlock-rework DESTRUCTION §6 (7,0): r3 final rank, see r1s note. Capstone: spell_warl_fury_of_the_void SpellScript on Shadowfury 30283 (WP-B, §7.13) - AddAura(348) on hit targets when the caster has this rank.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Shadowfury duration increased, Shadowfury/Shadowflame damage increased.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the duration of Shadowfury by $/1000;s1 seconds and increases the damage of your Shadowfury and Shadowflame by $s2%.\n\nCapstone Bonus: Your Shadowfury also afflicts all enemies hit with the periodic effect of your Immolate.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': m.SHADOWFURY, 'EffectSpellClassMaskB_2': m.SHADOWFURY | m.SHADOWFLAME, 'EffectSpellClassMaskC_3': m.SHADOWFLAME_DOT, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


chaotic_resonance_200975 = spell(
    id=200975,
    name='Chaotic Resonance',
    school=School.NORMAL,
    attributes=464,
    duration_ms=-1,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=108, misc_value=0),
    ],
    spell_icon_id=2352,
    notes='warlock-rework DESTRUCTION §6 (9,2) NEW talent 60103: ADD_PCT_MODIFIER DAMAGE (+2/4/6%), A_2 = CHAOS_BOLT (0x20000, reaches Rift Bolt + copies + echoes via shared family flags, G3).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Chaos Bolt damage increased by $s1%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Chaos Bolt by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Your Chaos Bolts and Chaos Rift Bolts have a 5% chance to fire a Chaos Echo, a copy of themselves, at the same target.|r', 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_2': m.CHAOS_BOLT, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


chaotic_resonance_200976 = spell(
    id=200976,
    name='Chaotic Resonance',
    school=School.NORMAL,
    attributes=464,
    duration_ms=-1,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=108, misc_value=0),
    ],
    spell_icon_id=2352,
    notes='warlock-rework DESTRUCTION §6 (9,2): r2, see r1s note.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Chaos Bolt damage increased by $s1%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Chaos Bolt by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Your Chaos Bolts and Chaos Rift Bolts have a 5% chance to fire a Chaos Echo, a copy of themselves, at the same target.|r', 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_2': m.CHAOS_BOLT, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


chaotic_resonance_200977 = spell(
    id=200977,
    name='Chaotic Resonance',
    school=School.NORMAL,
    attributes=464,
    duration_ms=-1,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=108, misc_value=0),
    ],
    spell_icon_id=2352,
    notes='warlock-rework DESTRUCTION §6 (9,2): r3 final rank, see r1s note. Chaos Echo roll happens in spell_warl_chaos_bolt (WP-B, §7.7) and the Rift AI (§7.2), reading this rank id.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Chaos Bolt damage increased by $s1%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Chaos Bolt by $s1%.\n\nCapstone Bonus: Your Chaos Bolts and Chaos Rift Bolts have a 5% chance to fire a Chaos Echo, a copy of themselves, at the same target.', 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_2': m.CHAOS_BOLT, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


# ---------------------------------------------------------------------------
# warlock-rework DESTRUCTION pass (S2) - Chaos Rift / Havoc / Chaos Bolt
# family (§5, §7.2/§7.5/§7.6/§7.7): Rift Bolt, the Havoc/Soulburn Chaos Bolt
# copy, both Chaos Echo strengths, and Chaotic Burn.
# ---------------------------------------------------------------------------

rift_bolt_200979 = spell(
    id=200979,
    name='Rift Bolt',
    school=36,  # Fire | Shadow (Shadowflame)
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=418, points_per_level=6.975, die_sides=113, implicit_target_a=6),
    ],
    spell_icon_id=3178,
    notes='warlock-rework DESTRUCTION §5/§7.2: 50% of the rebased Chaos Bolt (bp 418, ppl 6.975, die 113, Base/SpellLevel 60 - the Rift exists only from level 60; 419-531 @60, 558-670 @80 = half of Chaos Bolts own 837-1061/1116-1340). Cast by npc_warl_chaos_rift with the warlock as original caster (WP-B). range_yards 100 - the AI pre-filters to 40yd. Shares Chaos Bolts d2 0x20000 so Bane/Chaotic Resonance/Mastery reach it (G3); AttributesEx3 ALWAYS_HIT|SUPPRESS_CASTER_PROCS, AttributesEx4 as 50796 (absorb-pierce/resist-ignore inherited via 58284s SpellInfoCorrections).',
    raw_overrides={'AttributesEx3': 327680, 'AttributesEx4': 2048, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 19, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Deals $s1 Shadowflame damage. Cannot be resisted, and pierces through all absorption effects.', 'EffectBonusMultiplier_1': 0.357, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 20.0, 'SpellClassMask_2': m.CHAOS_BOLT, 'SpellClassSet': 5, 'SpellLevel': 60, 'SpellVisualID_1': 11240, 'StartRecoveryCategory': 0, 'StartRecoveryTime': 0},
)
scripted_by(rift_bolt_200979, 'spell_warl_chaos_bolt_mastery')


chaos_bolt_copy_200980 = spell(
    id=200980,
    name='Chaos Bolt',
    school=36,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=557, points_per_level=13.95, die_sides=225, implicit_target_a=6),
    ],
    spell_icon_id=3178,
    notes='warlock-rework DESTRUCTION §5/§7.5/§7.6: identical damage data to the rebased Chaos Bolt 50796 (bp 557, ppl 13.95, die 225, Base/SpellLevel 40, EffectBonusMultiplier 0.714). Cast for the Havoc duplicate and Soulburn: Chaos Bolts extra targets (WP-B); range_yards 30 so Destructive Reach and the engine range check enforce "within range". Shares Chaos Bolts d2 0x20000; triggered + SUPPRESS_CASTER_PROCS so it never re-rolls Soulburn/Chaotic Inferno/Intensity/Soul Leech/Chaos Echo (G3).',
    raw_overrides={'AttributesEx3': 327680, 'AttributesEx4': 2048, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 40, 'CastingTimeIndex': 19, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Deals $s1 Shadowflame damage. Cannot be resisted, and pierces through all absorption effects.', 'EffectBonusMultiplier_1': 0.7139999866485596, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 20.0, 'SpellClassMask_2': m.CHAOS_BOLT, 'SpellClassSet': 5, 'SpellLevel': 40, 'SpellVisualID_1': 11240, 'StartRecoveryCategory': 0, 'StartRecoveryTime': 0},
)
scripted_by(chaos_bolt_copy_200980, 'spell_warl_chaos_bolt_copy', 'spell_warl_chaos_bolt_mastery')


chaos_echo_200981 = spell(
    id=200981,
    name='Chaos Echo',
    school=36,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=557, points_per_level=13.95, die_sides=225, implicit_target_a=6),
    ],
    spell_icon_id=3178,
    notes='warlock-rework DESTRUCTION §5/§7.7 (Chaotic Resonance r3 200977): full-Chaos-Bolt-strength echo (200980s data, range widened to 100 since the echo re-targets the same unit, not a fresh cast). Shares Chaos Bolts d2 0x20000; SUPPRESS_CASTER_PROCS + triggered - never applies Chaotic Burn, never re-rolls Chaos Echo, never consumes Soulburn/Chaotic Inferno, never starts Chaos Bolts cooldown (QA #28).',
    raw_overrides={'AttributesEx3': 327680, 'AttributesEx4': 2048, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 40, 'CastingTimeIndex': 19, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Deals $s1 Shadowflame damage. Cannot be resisted, and pierces through all absorption effects.', 'EffectBonusMultiplier_1': 0.7139999866485596, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 20.0, 'SpellClassMask_2': m.CHAOS_BOLT, 'SpellClassSet': 5, 'SpellLevel': 40, 'SpellVisualID_1': 11240, 'StartRecoveryCategory': 0, 'StartRecoveryTime': 0},
)
scripted_by(chaos_echo_200981, 'spell_warl_chaos_bolt_mastery')


chaos_echo_200982 = spell(
    id=200982,
    name='Chaos Echo',
    school=36,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=418, points_per_level=6.975, die_sides=113, implicit_target_a=6),
    ],
    spell_icon_id=3178,
    notes='warlock-rework DESTRUCTION §5/§7.2/§7.7: Rift-Bolt-strength echo (200979s data, range_yards 100). Fired by npc_warl_chaos_rift for every bolt when the caster has Chaotic Resonance r3 (WP-B).',
    raw_overrides={'AttributesEx3': 327680, 'AttributesEx4': 2048, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 19, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Deals $s1 Shadowflame damage. Cannot be resisted, and pierces through all absorption effects.', 'EffectBonusMultiplier_1': 0.357, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 20.0, 'SpellClassMask_2': m.CHAOS_BOLT, 'SpellClassSet': 5, 'SpellLevel': 60, 'SpellVisualID_1': 11240, 'StartRecoveryCategory': 0, 'StartRecoveryTime': 0},
)
scripted_by(chaos_echo_200982, 'spell_warl_chaos_bolt_mastery')


chaotic_burn_200983 = spell(
    id=200983,
    name='Chaotic Burn',
    school=36,
    attributes=65536,
    duration_ms=6000,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    dispel=DispelType.MAGIC,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=2000),
    ],
    spell_icon_id=2299,
    notes="warlock-rework DESTRUCTION §5/§7.7: fixed base points from the script (CastCustomSpell BP0 = perTick, §7.7) - 3 ticks at 0 haste = 25% of the Chaos Bolt hit that applied it. No family bits (its own spell, not Chaos Bolts family). AttributesEx2 CANT_CRIT (already carries the triggering hits crit, §11 Q4) + AttributesEx3 IGNORE_CASTER_MODIFIERS (fixed base points). Base/SpellLevel 40.",
    raw_overrides={'AttributesEx2': 536870912, 'AttributesEx3': 536870912, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s1 Shadowflame damage every $t1 sec.', 'BaseLevel': 40, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': '$o1 Shadowflame damage over $d.', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 5, 'SpellLevel': 40},
)


molten_bolts_200984 = spell(
    id=200984,
    name='Molten Bolts',
    school=School.FIRE,
    attributes=65536,
    duration_ms=2000,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=6, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=500, trigger_spell=200985),
    ],
    spell_icon_id=2298,
    notes='warlock-rework DESTRUCTION §5/§7.14 (Kindling r3 capstone volley): 0.5s period over 2s = 4 bolts at 0.5/1.0/1.5/2.0s; not hasted (no ATTR5 flag, no periodic-damage effect so CalculatePeriodic leaves the amplitude alone) - fixed at 4 bolts regardless of haste (QA #23/#24 precedent). A new proc while bolts are firing restarts the volley (refresh resets the timer/counter). Stops when the target dies (aura falls off with the target).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Firing Molten Bolts.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Fires 4 Molten Bolts at the target, one every 0.5 sec, each dealing $200985s1 Fire damage.', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 5},
)


molten_bolt_200985 = spell(
    id=200985,
    name='Molten Bolt',
    school=School.FIRE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=6, points_per_level=0.671667, implicit_target_a=6),
    ],
    spell_icon_id=2298,
    notes='warlock-rework DESTRUCTION §5: 10% of the rebased Incinerate (bp 6, ppl 0.671667, Base/SpellLevel 10 - Kindling sits in tier 0): 7@10, 16@24, 40@60, 54@80 (10% of Incinerates 403@60/538@80). Speed 0 (instant hit, no missile travel time - triggered by the Molten Bolts aura, no family bit so it never rolls procs itself).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 10, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Deals $s1 Fire damage.', 'EffectBonusMultiplier_1': 0.0714, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 0.0, 'SpellClassMask_3': m.MOLTEN_BOLT, 'SpellClassSet': 5, 'SpellLevel': 10, 'StartRecoveryCategory': 0, 'StartRecoveryTime': 0},
)


immolate_eruption_200986 = spell(
    id=200986,
    name='Immolate Eruption',
    school=School.FIRE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    radius_yards=5.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, implicit_target_a=53, implicit_target_b=16, radius_yards=5.0),
    ],
    spell_icon_id=31,
    notes='warlock-rework DESTRUCTION §5/§7.10 (Improved Immolate r3 capstone): fixed base points from the script (CastCustomSpell BP0 = the tick snapshot / 2, §7.10). AttributesEx3 IGNORE_CASTER_MODIFIERS|SUPPRESS_CASTER_PROCS (fixed damage, no procs). OnObjectAreaTargetSelect drops units not IsInCombatWith(caster); the source target is included (C3, QA #25).',
    raw_overrides={'AttributesEx3': 536936448, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Deals $s1 Fire damage to all enemies within 5 yards of the target that are in combat with you.', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 5, 'StartRecoveryCategory': 0, 'StartRecoveryTime': 0},
)
scripted_by(immolate_eruption_200986, 'spell_warl_immolate_eruption')


chaotic_inferno_200987 = spell(
    id=200987,
    name='Chaotic Inferno',
    school=School.FIRE,
    attributes=65536,
    duration_ms=15000,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=RANGE_SELF,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3178,
    notes='warlock-rework DESTRUCTION §5 (Devastation r3 capstone): self marker, no charges (the arbiter grants/consumes it, §7.6). Registered as InstantCastSource.ChaoticInferno for base spell 50796.',
    raw_overrides={'AttributesEx': 131072, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next Chaos Bolt is instant.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your next Chaos Bolt is instant.', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


intensity_200988 = spell(
    id=200988,
    name='Intensity',
    school=School.NORMAL,
    attributes=65536,
    duration_ms=8000,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=RANGE_SELF,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL),
    ],
    spell_icon_id=876,
    notes='warlock-rework DESTRUCTION §5 (Intensity r2 capstone buff): self, +15% haste for 8s. Granted by intensity_18136s PROC_TRIGGER_SPELL row.',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx5': 8192, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Haste increased by $s1%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your haste by $s1% for $d.', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)


hellstorm_200989 = spell(
    id=200989,
    name='Hellstorm',
    school=School.FIRE,
    attributes=65536,
    duration_ms=8000,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=RANGE_SELF,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2385,
    notes='warlock-rework DESTRUCTION §5/§7.4 (Hellstorm r3 capstone buff): self, drives the Hellfire tick-rate injection (Warlock::StartHellstormAcceleration, WP-B). bp 49 -> displays 50 (the +50% rate, informational only - the actual acceleration is scripted).',
    raw_overrides={'AttributesEx': 131072, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Hellfire ticks $s1% faster.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Hellfire ticks $s1% faster. Your damage taken from Hellfire per second is unchanged.', 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 5},
)
scripted_by(hellstorm_200989, 'spell_warl_hellstorm')
scripted_by(1949, 'spell_warl_hellfire_hellstorm')


fire_and_brimstone_200990 = spell(
    id=200990,
    name='Fire and Brimstone',
    school=School.FIRE,
    attributes=65536,
    duration_ms=30000,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=6, apply_aura=AuraType.MOD_DAMAGE_FROM_CASTER),
    ],
    spell_icon_id=3173,
    notes="warlock-rework DESTRUCTION §5/§7.14 (Fire and Brimstone r3 capstone stacks): target debuff, per caster, aura 271 (5% per stack, bp 4 -> displays 5), EffectSpellClassMaskA_2 = SOUL_FIRE (0x80, the only spell it boosts). CumulativeAura 10 (max +50%). 30s duration, refreshed per stack (§11 Q6). A debuff, not a talent rank - C4 only scans the casters own DUMMY auras, so this carries no DUMMY effect.",
    raw_overrides={'AttributesEx3': 128, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Takes $s1% increased damage from the warlocks next Soul Fire.', 'CastingTimeIndex': 1, 'CumulativeAura': 10, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases damage taken from the warlocks next Soul Fire by $s1%. Stacks up to 10.', 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_2': m.SOUL_FIRE, 'EquippedItemClass': -1, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 5},
)


destructive_reach_crit_200991 = spell(
    id=200991,
    name='Destructive Reach',
    school=School.NORMAL,
    attributes=0x180,  # hidden helper convention (DESTRUCTION.md §5): 0x80 | 0x100, no NOT_SHAPESHIFTED - never cast from the spellbook
    duration_ms=10000,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=RANGE_SELF,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=160,
    notes='warlock-rework DESTRUCTION §5/§7.9 (C3, Destructive Reach r2 capstone helper): hidden 1-charge ADD_FLAT_MODIFIER CRITICAL_CHANCE (+4%), SpellClassSet 5 with an all-effect-index class mask (letter A = effect index 0) of WARLOCK_PLAYER_DAMAGE_FULL (WP-A OR-term: Destruction scope | REACH_SPELLS, _masks.py). ProcCharges 1, ProcTypeMask 0 so no auto-generated spell_proc row eats the charge (SpellMgr.cpp:2159-2239 / Player.cpp:10253). Granted/removed by Warlock::ApplyDestructiveReachCrit in the shared CanPrepare handler (WP-B).',
    raw_overrides={'AttributesEx4': 0, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Critical strike chance increased by 4% against distant enemies.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell critical strike chance by 4% against enemies farther than 20 yards away.', 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': m.WARLOCK_PLAYER_DAMAGE_FULL[0], 'EffectSpellClassMaskA_2': m.WARLOCK_PLAYER_DAMAGE_FULL[1], 'EffectSpellClassMaskA_3': m.WARLOCK_PLAYER_DAMAGE_FULL[2], 'EquippedItemClass': -1, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcCharges': 1, 'ProcChance': 101, 'ProcTypeMask': 0, 'RangeIndex': 1, 'SpellClassSet': 5},
)


instant_cast_helper_200713 = spell(
    id=200713,
    name='Instant Cast',
    school=School.NORMAL,
    attributes=0x180,
    duration_ms=10000,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=RANGE_SELF,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=108, misc_value=10),
    ],
    spell_icon_id=160,
    notes='warlock-rework DESTRUCTION §0.3/§5 (SHARED §1.3 id, declared here per the reconciled ownership - AFFLICTION.md §0.4 item 11 / WP-0 item 6 defer this row to Destruction): hidden 1-charge ADD_PCT_MODIFIER CASTING_TIME -100% (the Backlash 34936 shape). Mask = Soul Fire d2 0x80 | Chaos Bolt d2 0x20000 (INSTANT_CAST_HELPER) - both Soul Fire sources (Empowered Imp, Soulburn) and Chaos Bolts Soulburn/Chaotic Inferno sources are registered in this pass. ProcCharges 1, ProcTypeMask 0 (no auto spell_proc row, same reasoning as 200991). Granted/consumed solely by the Affliction-built CanPrepare/OnSpellCast arbiter (§7.6).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next qualifying cast is instant.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your next qualifying cast is instant.', 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_2': m.INSTANT_CAST_HELPER[1], 'EquippedItemClass': -1, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcCharges': 1, 'ProcChance': 101, 'ProcTypeMask': 0, 'RangeIndex': 1, 'SpellClassSet': 5},
)
