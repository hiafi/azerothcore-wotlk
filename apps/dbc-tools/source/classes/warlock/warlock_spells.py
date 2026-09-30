"""
Warlock - player-castable spells (real cast_time_ms/cooldown_ms, not marked passive).

Split from a single source/classes/warlock.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .warlock_...` below) resolve.
"""

from lib.dsl import AuraType, DispelType, Effect, EffectType, Mechanic, PowerType, RANGE_SELF, School
from lib.dsl.registry import bonus_coefficients, creature_model, creature_template, custom_attr, linked_spell, procs_on, scripted_by, shapeshift_form, skill_line_ability, spell, spell_group, spell_group_rule, trained_by, unbind_script, untrain
from .warlock_trigger_spells import hellfire_effect_5857
from . import _masks as m


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
    duration_ms=18000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, points_per_level=1.5222222222222221, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=2000),
        Effect(type=EffectType.DUMMY, die_sides=0),
    ],
    spell_icon_id=313,
    notes='warlock-rework AFFLICTION §4.1 B8 bootstrap restore: 18s/9 ticks at the stock max-rank total (1.2 SP over the DoT), per-tick base rescaled via B3 (V60=91.33) from learn level 4 -> 6 @4, 91 @60, 121 @80; coefficient restored to 0.1333/tick (bonus_coefficients below)',
    raw_overrides={'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s1 Shadow damage every $t1 seconds.', 'BaseLevel': 4, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Corrupts the target, causing $o1 Shadow damage over $d.', 'EffectBonusMultiplier_1': 0.1333, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 2, 'SpellClassSet': 5, 'SpellLevel': 4, 'SpellPriority': 50, 'SpellVisualID_1': 8629, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
bonus_coefficients(corruption_172, dot=0.1333, comment='warlock-rework AFFLICTION §4.1 B8 - restore stock max-rank Corruption coefficient (1.2 SP total / 9 ticks)')
scripted_by(corruption_172, 'spell_warl_corruption_affliction')


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
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_DAMAGE_FROM_CASTER),
    ],
    spell_icon_id=31,
    notes="pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 11 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. warlock-rework AFFLICTION §4.1 B8 item 2: DoT coefficient (EffectBonusMultiplier_1) restored to 0.2 - its spell_bonus_data row was deleted by 2026_09_01_26.sql, leaving the DoT with no SP scaling. warlock-rework DESTRUCTION §0.1.2/§6 (9,1), C4 replacement: eff2 (previously unused SCRIPT_EFFECT, no binding anywhere) rewritten to APPLY_AURA MOD_DAMAGE_FROM_CASTER (271), bp -1 die 1 (= 0 without Fire and Brimstone), C = FNB_IMMOLATE_BONUS (Incinerate, Soul Fire, Chaos Bolt + copies) - raised to 3/6/10% by Fire and Brimstone's flat SPELLMOD_EFFECT3 (47266-68).",
    raw_overrides={'AttributesEx4': 1048576, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s1 Fire damage every $t1 seconds.', 'BaseLevel': 1, 'CastingTimeIndex': 5, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Burns the enemy for $s2 Fire damage and then an additional $o1 Fire damage over $d.', 'EffectBonusMultiplier_1': 0.2, 'EffectBonusMultiplier_2': 0.20000000298023224, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskC_1': m.FNB_IMMOLATE_BONUS[0], 'EffectSpellClassMaskC_2': m.FNB_IMMOLATE_BONUS[1], 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 4, 'SpellClassSet': 5, 'SpellLevel': 1, 'SpellVisualID_1': 46, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
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
# warlock-rework DEMONOLOGY §4.6: Curse of Doom removed, replaced by Bane of Doom 200825. No data
# edit (the stock spell_warl_curse_of_doom -603 binding stays and is unreachable) - just untrain it.
untrain(curse_of_doom_603, trainer_ids=[214])


shadow_bolt_686 = spell(
    id=686,
    name='Shadow Bolt',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=2000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=17,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=11, points_per_level=7.966101694915254, die_sides=5, implicit_target_a=6),
    ],
    spell_icon_id=213,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60 (anchor rank 10 @ level 60); coefficient/mana_cost_pct from max rank; MaxLevel set to 80. PLAN A9 (druid-rework code review finding #9): cast_time_ms=2000, raw CastingTimeIndex (90, 1700ms) dropped.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Sends a shadowy bolt at the enemy, causing $s1 Shadow damage.', 'EffectBonusMultiplier_1': 0.8569999933242798, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 20.0, 'SpellClassMask_1': 1, 'SpellClassSet': 5, 'SpellLevel': 1, 'SpellVisualID_1': 64, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
scripted_by(shadow_bolt_686, 'spell_warl_shadow_bolt_affliction', 'spell_warl_shadow_bolt_demonology')


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
scripted_by(drain_life_689, 'spell_warl_drain_life_affliction')


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
    raw_overrides={'AttributesEx': 131072, 'AttributesEx4': 65536, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 18, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Creates a Minor Soulstone.  The Soulstone can be used to store one target's soul.  If the target dies while his soul is stored, he will be able to resurrect with $3026s1 health and $3026q1 mana.\r\n\r\nConjured items disappear if logged out for more than 15 minutes.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 5232, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ReagentCount_1': 0, 'Reagent_1': 0, 'SpellClassMask_1': 1048576, 'SpellClassSet': 5, 'SpellLevel': 18, 'SpellVisualID_1': 138, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
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
    raw_overrides={'AttributesEx': 131076, 'AttributesEx3': 1073741824, 'AttributesEx4': 65536, 'AttributesEx5': 8192, 'AttributesEx6': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 15374, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Begins a ritual that creates a summoning portal.  The summoning portal can be used by 2 party or raid members to summon a targeted party or raid member.  The ritual portal requires the caster and 2 additional party or raid members to complete.  In order to participate, all players must be out of combat and right-click the portal and not move until the ritual is complete.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectRadiusIndex_1': 36, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 0, 'Reagent_1': 0, 'SpellClassMask_3': 64, 'SpellClassSet': 5, 'SpellLevel': 20, 'SpellVisualID_1': 1523, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
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


bane_of_agony_980 = spell(
    id=980,
    name='Bane of Agony',
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
        Effect(type=EffectType.APPLY_AURA, base_points=11, points_per_level=1.45, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=2000),
    ],
    spell_icon_id=544,
    notes='warlock-rework AFFLICTION §4.5 B14: renamed from Curse of Agony (banes stay Dispel=Curse but leave the curse slot - B14); per-tick base rescaled via B3 to spec B5s numbers (V60=87) -> 12@8, 87@60, 116@80; the stack ramp lives on this aura itself (CumulativeAura 15 = max cap with Improved Curses r2; live cap via Warlock::GetAgonyStackCap) so the target shows one debuff with a stack count - spell_warl_bane_of_agony_aura keeps its own 1-stack snapshot and writes snapshot x (1 + 0.1 x stacks) before each tick, and the SpellScript undoes the +1 stack a recast adds (recast still re-snapshots, R2). Replaces the old separate 200720 tracker.',
    raw_overrides={'AttributesEx3': 128, 'AttributesEx4': 1048576, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s1 Shadow damage every $t1 sec, increased by 10% per stack.', 'BaseLevel': 8, 'CastingTimeIndex': 1, 'CumulativeAura': 15, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Afflicts the target with agony, causing $o1 Shadow damage over $d.  Each tick adds a stack that increases its damage by 10%, up to 10 stacks.  Only one Bane per Warlock can be active on any one target.', 'EffectBonusMultiplier_1': 0.10000000149011612, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 1024, 'SpellClassSet': 5, 'SpellLevel': 8, 'SpellVisualID_1': 824, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
scripted_by(bane_of_agony_980, 'spell_warl_bane_of_agony')
unbind_script(-980, 'spell_warl_curse_of_agony')
spell_group(1202, bane_of_agony_980)
spell_group_rule(1202, 2, 'Warlock - bane slot (one bane per caster per target)')


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
    raw_overrides={'AttributesEx': 131073, 'AttributesEx2': 64, 'AttributesEx4': 536872960, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Enslaved.', 'BaseLevel': 30, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Enslaves the target demon, up to level $m1, forcing it to do your bidding.  While enslaved, the time between the demon's attacks is increased by $s2% and its casting speed is slowed by $s3%.  Lasts up to $d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 0, 'Reagent_1': 0, 'SpellClassMask_1': 2048, 'SpellClassSet': 5, 'SpellLevel': 30, 'SpellVisualID_1': 1266, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetCreatureType': 4},
)
scripted_by(enslave_demon_1098, 'spell_warl_enslave_demon_potency')


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
        Effect(type=EffectType.APPLY_AURA, base_points=0, die_sides=0, implicit_target_a=6, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=10, points_per_level=1.8714285714285714, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL),
    ],
    spell_icon_id=113,
    notes='warlock-rework AFFLICTION §4.2 B9: eff1 aura 86 (CHANNEL_DEATH_ITEM, drops a Soul Shard item) replaced by DUMMY - shard generation moves to the Soul Shard buff (200709), granted by spell_warl_drain_soul_affliction on kill',
    raw_overrides={'AttributesEx': 67256324, 'AttributesEx3': 134217728, 'AttributesEx5': 8192, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s2 Shadow damage every $t2 seconds.', 'BaseLevel': 10, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31756, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Drains the soul of the target, causing $o2 Shadow damage over $d.  If the target is at or below 25% health, Drain Soul causes four times the normal damage. If the target dies while being drained, and yields experience or honor, you gain a Soul Shard.', 'EffectBonusMultiplier_2': 0.42899999022483826, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 2, 'SpellClassMask_1': 16384, 'SpellClassSet': 5, 'SpellLevel': 10, 'SpellVisualID_1': 12656, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
scripted_by(drain_soul_1120, 'spell_warl_drain_soul_affliction')
unbind_script(-1120, 'spell_warl_drain_soul')


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
    raw_overrides={'AttributesEx': 131072, 'AttributesEx5': 2, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 36, 'CastingTimeIndex': 6, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While applied to target weapon it increases damage dealt by periodic spells by $55172s1% and spell haste rating by $55172s3.  Lasts for 1 hour.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 41191, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ReagentCount_1': 0, 'Reagent_1': 0, 'SpellClassMask_1': 1048576, 'SpellClassSet': 5, 'SpellLevel': 36, 'SpellVisualID_1': 138, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


firebolt_3110 = spell(
    id=3110,
    name='Firebolt',
    school=School.FIRE,
    attributes=65536,
    cast_time_ms=2000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=5, points_per_level=2.4936708860759493, die_sides=3, implicit_target_a=6),
    ],
    spell_icon_id=18,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/mana_cost_pct from max rank; MaxLevel set to 80. PLAN A9 (druid-rework code review finding #9): keeps its live cast time - cast_time_ms=2000, raw CastingTimeIndex (5, 2000ms) dropped; no behaviour change.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Deals $s1 Fire damage to a target.', 'EffectBonusMultiplier_1': 0.7139999866485596, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 16.0, 'SpellClassMask_1': 4096, 'SpellClassSet': 5, 'SpellLevel': 1, 'SpellVisualID_1': 67, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
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
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=22, implicit_target_b=15, apply_aura=AuraType.MOD_FEAR, radius_yards=10.0),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=22, implicit_target_b=15, apply_aura=AuraType.MOD_INCREASE_SPEED, radius_yards=10.0),
    ],
    spell_icon_id=134,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 40); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. warlock-rework AFFLICTION §4.1 B8: duration restored to stock max rank (8s).',
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
    cast_time_ms=2000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=57,
    range_yards=30.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.PERSISTENT_AREA_AURA, base_points=35, points_per_level=6.17, implicit_target_a=28, apply_aura=AuraType.DUMMY, radius_yards=8.0),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=2000),
    ],
    spell_icon_id=547,
    notes="warlock-rework DESTRUCTION §4.2 (B18 + R5 + C5): no longer a channel (AttributesEx 0x1000008C -> 0x00000088, clearing SPELL_ATTR1_IS_CHANNELED and SPELL_ATTR1_NO_AURA_ICON), 2s cast, ChannelInterruptFlags cleared; eff0 is the ground-effect snapshot source (bp/ppl x0.6 of the old channel values, EffectBonusMultiplier_1 0.6x0.286=0.1716) read by spell_warl_rain_of_fire's AuraScript at AfterEffectApply; eff1 unchanged (2s PERIODIC_DUMMY, hasted at cast via AttributesEx5 0x2000). Learn level/BaseLevel unchanged at 20 (B18 does not rebase RoF).",
    raw_overrides={'AttributesEx': 136, 'AttributesEx2': 4194304, 'AttributesEx5': 8192, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Raining fire on the target area.', 'BaseLevel': 20, 'CastingTimeIndex': 5, 'ChannelInterruptFlags': 0, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Calls down a fiery rain at the target location for $d, burning enemies within $a1 yards for $42223s1 Fire damage every $42223t1 sec. Only one of your Rain of Fire can be active at a time.', 'EffectBonusMultiplier_1': 0.1716, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 32, 'SpellClassSet': 5, 'SpellLevel': 20, 'SpellVisualID_1': 10379, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Targets': 64},
)
scripted_by(rain_of_fire_5740, 'spell_warl_rain_of_fire')


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
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_FEAR),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=6, apply_aura=AuraType.MOD_INCREASE_SPEED),
    ],
    spell_icon_id=98,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 8); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. warlock-rework AFFLICTION §4.1 B8: duration restored to stock max rank (20s).',
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
    raw_overrides={'AttributesEx': 268566528, 'AttributesEx5': 2, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 10, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Creates a Minor Healthstone that can be used to instantly restore $6262s1 health.\r\n\r\nConjured items disappear if logged out for more than 15 minutes.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ReagentCount_1': 0, 'ReagentCount_2': 1, 'Reagent_1': 0, 'Reagent_2': -2, 'SpellClassMask_1': 1048576, 'SpellClassSet': 5, 'SpellLevel': 10, 'SpellVisualID_1': 138, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
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
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=437, points_per_level=14.338983050847457, die_sides=8, implicit_target_a=6),
    ],
    spell_icon_id=184,
    notes="warlock-rework DEMONOLOGY §4.4/§0.1.7: learn level 48 -> 30, rebased on _scaling.sb_units(1.8, 30, 868, 875) (k=1.8 x Shadow Bolt). EffectBonusMultiplier_1 = 1.8 x SB_COEF (0.857) = 1.5426. Cast time/mana_cost_pct unchanged (3.3.5 values). trained_by replaces the old 48/14000 row below.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 30, 'CastingTimeIndex': 171, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Burn the enemy's soul, causing $s1 Fire damage.", 'EffectBonusMultiplier_1': 1.5426, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 0, 'Reagent_1': 0, 'Speed': 24.0, 'SpellClassMask_2': 128, 'SpellClassSet': 5, 'SpellLevel': 30, 'SpellVisualID_1': 2253, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
scripted_by(soul_fire_6353, 'spell_warl_soul_fire_destruction', 'spell_warl_soul_fire_demonology')
trained_by(soul_fire_6353, 214, 30, 6000)


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
    raw_overrides={'AttributesEx': 131072, 'AttributesEx5': 2, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 28, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While applied to target weapon it increases damage dealt by direct spells by 1% and spell critical strike rating by $55146s3.  Lasts for 1 hour.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 41170, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ReagentCount_1': 0, 'Reagent_1': 0, 'SpellClassMask_1': 1048576, 'SpellClassSet': 5, 'SpellLevel': 28, 'SpellVisualID_1': 4800, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
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
scripted_by(death_coil_6789, 'spell_warl_harvester_death_coil')


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
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 36); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80; warlock-rework classmask-scope-audit Bug B: added SpellClassMask_3=SPELL_LOCK (stock row shipped with no family flag, so Improved Felhunter\'s "and Spell Lock" cooldown clause matched nothing)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 36, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Silences the enemy for $24259d.  If used on a casting target, it will counter the enemy's spellcast, preventing any spell from that school of magic from being cast for $d.", 'EffectBonusMultiplier_2': 0.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_3': m.SPELL_LOCK, 'SpellClassSet': 5, 'SpellLevel': 36, 'SpellPriority': 50, 'SpellVisualID_1': 5282},
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
        Effect(type=EffectType.APPLY_AURA, base_points=127, points_per_level=2.9, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
        Effect(type=EffectType.APPLY_AURA, base_points=834, points_per_level=18.975, implicit_target_a=6, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1932,
    notes='warlock-rework AFFLICTION §4.1 B8/B16/§11 Q5: learn level rebased 70->44 (docs/spell_learn_level.md), trainer 214 added (§4.7); DoT rebased via B3 (V60=174, today) -> 128@44/174@60/232@80; damage threshold kept on B8s explicit level-80 anchor (1518@80) -> 835@44/1138@60/1518@80; SpellClassMask_2 rebit 0x10->0x4 (B16, DoT only - detonation 27285 keeps 0x10)',
    raw_overrides={'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': "Causes $s1 Shadow damage every $t1 sec.  After taking $s2 total damage or dying, Seed of Corruption deals $27285s1 Shadow damage to the caster's enemies within $27285a1 yards.", 'AuraInterruptFlags': 1073741824, 'BaseLevel': 44, 'CastingTimeIndex': 5, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Imbeds a demon seed in the enemy target, causing $27243o1 Shadow damage over $27243d.  When the target takes $27243s2 total damage or dies, the seed will inflict $27285s1 Shadow damage to all enemies within $27285a1 yards of the target.', 'EffectBonusMultiplier_1': 0.25, 'EffectBonusMultiplier_2': 0.14300000667572021, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 664232, 'Speed': 28.0, 'SpellClassMask_2': 4, 'SpellClassSet': 5, 'SpellLevel': 44, 'SpellVisualID_1': 8339, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
scripted_by(seed_of_corruption_27243, 'spell_warl_seed_of_corruption_soulburn')
trained_by(seed_of_corruption_27243, trainer_id=214, req_level=44, money_cost=12000)


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
        Effect(type=EffectType.APPLY_AURA, base_points=34, points_per_level=0.8333333, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_DONE, misc_value=126),
    ],
    spell_icon_id=2297,
    notes='warlock-rework AFFLICTION §4.7 (user 2026-09-27, docs/spell_learn_level.md): baseline learn level 42, trainer 214 added; eff2 (flat spell power) rebased via B3 (V60=50) -> 35@42, 50@60, 66@80',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases spell power by $s3 plus additional spell power equal to $s1% of your Spirit. Also regenerate $s2% of maximum health every 5 sec.', 'BaseLevel': 42, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Surrounds the caster with fel energy, increasing spell power by $s3 plus additional spell power equal to $s1% of your Spirit. In addition, you regain $s2% of your maximum health every 5 sec. Only one type of Armor spell can be active on the Warlock at any time.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 4, 'EffectSpellClassMaskB_1': 524296, 'EffectSpellClassMaskB_2': 1, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 536870912, 'SpellClassSet': 5, 'SpellLevel': 42, 'SpellVisualID_1': 7578, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
trained_by(fel_armor_28176, trainer_id=214, req_level=42, money_cost=11000)


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
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=161, points_per_level=6.716667, die_sides=65, implicit_target_a=6),
    ],
    spell_icon_id=90170,
    notes='warlock-rework DESTRUCTION §4.1 (B3 rebase, learn level 64->24): bp/ppl rescaled so the level-60 value is unchanged (162-226 @24, 403-467 @60, 538-602 @80, -7.6% vs todays @80 - the BaseLevel-clamp artifact B3 accepts); coefficient/cast_time_ms/mana_cost_pct unchanged. Icon moved off 2128 to 90170 (B17(b)/C11 - makes the stock "+25% vs Immolate" hardcode inert; Fire and Brimstone (9,1) owns that bonus now via Immolate eff2). Description drops the stock $/4;s1 Immolate clause.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 24, 'CastingTimeIndex': 19, 'CumulativeAura': 5, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Deals $s1 Fire damage to your target.', 'EffectBonusMultiplier_1': 0.7139999866485596, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 4, 'EffectSpellClassMaskC_1': 4, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 1, 'Speed': 20.0, 'SpellClassMask_2': 64, 'SpellClassSet': 5, 'SpellLevel': 24, 'SpellVisualID_1': 7675, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
trained_by(incinerate_29722, trainer_id=214, req_level=24, money_cost=3000)


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
    notes='warlock-rework AFFLICTION §4.7/§4.2 B9: learn level rebased 68->48, trainer 214 added; reagent 6265 stripped (B9)',
    raw_overrides={'AttributesEx': 131076, 'AttributesEx5': 8194, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 48, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 572430, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Begins a ritual that creates a Soulwell.  Raid members can click the Soulwell to acquire a Master Healthstone.  The Soulwell lasts for $29886d or 25 charges.  Requires the caster and 2 additional party members to complete the ritual.  In order to participate, all players must right-click the soul portal and not move until the ritual is complete.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 31, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 0, 'Reagent_1': 0, 'SpellClassMask_2': 2147483648, 'SpellClassSet': 5, 'SpellLevel': 48, 'SpellPriority': 50, 'SpellVisualID_1': 7963, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
trained_by(ritual_of_souls_29893, trainer_id=214, req_level=48, money_cost=14000)


ritual_of_doom_18540 = spell(
    id=18540,
    name='Ritual of Doom',
    school=32,
    attributes=33619968,
    cast_time_ms=10000,
    cooldown_ms=1800000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=80,
    range_yards=30.0,
    duration_ms=60000,
    effects=[
        Effect(type=50, implicit_target_a=47, misc_value=177193, radius_yards=5.0),
    ],
    spell_icon_id=99,
    notes='warlock-rework: migrated from legacy npc.csv; reagent 16583 (Demonic Figurine) stripped',
    raw_overrides={'AttributesEx': 131077, 'AttributesEx5': 8192, 'CastingTimeIndex': 7, 'InterruptFlags': 31, 'ChannelInterruptFlags': 48142, 'ProcChance': 101, 'BaseLevel': 60, 'SpellLevel': 60, 'Reagent_1': 0, 'ReagentCount_1': 0, 'EquippedItemClass': -1, 'SpellVisualID_1': 4963, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': "Begins a ritual that sacrifices a random participant's health to summon a doomguard. Requires the caster and 4 additional party members to complete the ritual.  In order to participate, all players must right-click the portal and not move until the ritual is complete.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'SpellClassSet': 5, 'SpellClassMask_3': 64, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_2': 1.0},
)


inferno_1122 = spell(
    id=1122,
    name='Inferno',
    school=32,
    attributes=65536,
    category=731,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=600000,
    mana_cost=0,
    mana_cost_pct=80,
    range_yards=30.0,
    duration_ms=60000,
    effects=[
        Effect(type=28, base_points=49, points_per_level=1.0, implicit_target_a=16, misc_value=89, radius_yards=10.0),
        Effect(type=64, base_points=-1, implicit_target_a=87, trigger_spell=22703),
    ],
    spell_icon_id=460,
    notes='warlock-rework: migrated from legacy generic.csv; reagent 5565 (Infernal Stone) stripped',
    raw_overrides={'AttributesEx': 131073, 'AttributesEx2': 524288, 'AttributesEx4': 65536, 'ShapeshiftMask': 2097152, 'Targets': 64, 'CastingTimeIndex': 16, 'InterruptFlags': 15, 'ProcChance': 101, 'BaseLevel': 50, 'SpellLevel': 50, 'Reagent_1': 0, 'ReagentCount_1': 0, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 711, 'SpellVisualID_1': 4859, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Summon', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a meteor from the Twisting Nether, causing $22699s1 Fire damage and stunning all enemy targets in the area for $20310d.  An Infernal rises from the crater, under the command of the caster for $20882d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0},
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
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=433, points_per_level=8.666667, die_sides=49, implicit_target_a=104, radius_yards=10.0),
    ],
    spell_icon_id=3317,
    notes='warlock-rework DESTRUCTION §4.1 (B3 rebase, learn level 75->50): bp/ppl rescaled so the level-60 value is unchanged (434-482 @50, 520-568 @60, 694-742 @80, +13% vs todays @80 - the BaseLevel-clamp artifact B3 accepts); coefficient/cast_time_ms/mana_cost_pct unchanged.',
    raw_overrides={'AttributesEx': 136, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 50, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Targets in a cone in front of the caster take $47897s1 Shadow damage and an additional $47960o1 Fire damage over $47960d.', 'EffectBonusMultiplier_1': 0.10700000077486038, 'EffectBonusMultiplier_2': 0.10700000077486038, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'RangeIndex': 1, 'SpellClassMask_2': 65536, 'SpellClassSet': 5, 'SpellLevel': 50, 'SpellPriority': 50, 'SpellVisualID_1': 10689, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
trained_by(shadowflame_47897, trainer_id=214, req_level=50, money_cost=15000)


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
    notes='warlock-rework AFFLICTION §4.7 (user 2026-09-27): baseline learn level 54, trainer 214 added',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx4': 4, 'AttributesEx5': 516, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Demonic Circle Summoned.', 'AuraInterruptFlags': 4718592, 'BaseLevel': 54, 'CastingTimeIndex': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You summon a Demonic Circle at your feet, lasting $d. You can only have one Demonic Circle active at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_3': 32, 'SpellClassSet': 5, 'SpellLevel': 54, 'SpellVisualID_1': 10677, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
trained_by(demonic_circle_summon_48018, trainer_id=214, req_level=54, money_cost=20000)


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
    notes='warlock-rework AFFLICTION §4.7 (user 2026-09-27): baseline learn level 54, trainer 214 added',
    raw_overrides={'AttributesEx': 268599296, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 54, 'CasterAuraSpell': 62388, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Teleports you to your Demonic Circle and removes all snare effects.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_3': 32, 'SpellClassSet': 5, 'SpellLevel': 54, 'SpellVisualID_1': 10694, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
trained_by(demonic_circle_teleport_48020, trainer_id=214, req_level=54, money_cost=20000)


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
scripted_by(shadow_bite_54049, 'spell_warl_shadow_bite_improved_felhunter')
scripted_by(54050, 'spell_warl_shadow_bite_improved_felhunter')
scripted_by(54051, 'spell_warl_shadow_bite_improved_felhunter')
scripted_by(54052, 'spell_warl_shadow_bite_improved_felhunter')
scripted_by(54053, 'spell_warl_shadow_bite_improved_felhunter')


shadowburn_17877 = spell(
    id=17877,
    name='Shadowburn',
    school=36,  # School.FIRE | School.SHADOW (Shadowflame, DESTRUCTION §0.2.5)
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
    notes="warlock-rework DESTRUCTION §0.2.6/§4.1/§9: school Shadow(32)->36 (Fire|Shadow, Shadowflame). TargetAuraState 13 (AURA_STATE_HEALTHLESS_35_PERCENT, Unit.cpp:644) added - client-visible, greys out above 35% health, DESTRUCTION.md §0.2.6. Reagent already stripped by Affliction's B9. Description matches the new <35% clause; spell_warl_shadowburn_destruction (WP-B) is bound additively on debuff 29341 alongside Affliction's shard-generation replacement.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Instantly blasts the target for $s2 Shadowflame damage. Only usable against enemies below 35% health. If the target dies within $29341d and yields experience or honor, Shadowburn's cooldown is reset.", 'EffectBonusMultiplier_2': 0.42899999022483826, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 0, 'Reagent_1': 0, 'SpellClassMask_1': 128, 'SpellClassSet': 5, 'SpellLevel': 20, 'SpellVisualID_1': 3057, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetAuraState': 13},
)
# WP brief §6.2: the script binds the debuff 29341 (bare id), additively alongside Affliction's
# shard-generation replacement already bound there - not 17877 itself.
scripted_by(29341, 'spell_warl_shadowburn_destruction')


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
        Effect(type=EffectType.APPLY_AURA, base_points=99, points_per_level=2.5, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
        Effect(type=77, die_sides=0, implicit_target_a=6),
    ],
    spell_icon_id=2039,
    notes='warlock-rework AFFLICTION §4.7/§6 (6,1): moved from row 8 (level 50) to row 6 (level 40); rebased via B3 (V60=150, todays) -> 100@40, 150@60, 200@80 (was 230@80).',
    raw_overrides={'AttributesEx4': 1048576, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s1 Shadow damage every $t1 sec.  If dispelled, will cause $*9;s1 damage to the dispeller and silence them for $31117d.', 'BaseLevel': 40, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shadow energy slowly destroys the target, causing $o1 damage over $d.  In addition, if the Unstable Affliction is dispelled it will cause $*9;s1 damage to the dispeller and silence them for $31117d. Only one Unstable Affliction or Immolate per Warlock can be active on any one target.', 'EffectBonusMultiplier_1': 0.20000000298023224, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 256, 'SpellClassSet': 5, 'SpellLevel': 40, 'SpellPriority': 50, 'SpellVisualID_1': 8141, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
scripted_by(unstable_affliction_30108, 'spell_warl_unstable_affliction_affliction')


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
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=367, points_per_level=9.183333, die_sides=65, implicit_target_a=16, radius_yards=8.0),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, mechanic=Mechanic.STUN, implicit_target_a=16, apply_aura=AuraType.MOD_STUN, radius_yards=8.0),
    ],
    spell_icon_id=1988,
    notes='warlock-rework DESTRUCTION §4.1 (B3 rebase, moved (8,1)->(6,0), learn level 50->40): bp/ppl rescaled so the level-60 value is unchanged (368-432 @40, 551-615 @60, 735-799 @80, -24% vs todays @80); coefficient/cast_time_ms/mana_cost_pct/cooldown/range unchanged. Fury of the Void (7,0) capstone script bound on this id (WP-B).',
    raw_overrides={'AttributesEx': 136, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Stunned.', 'BaseLevel': 40, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shadowfury is unleashed, causing $s1 Shadow damage and stunning all enemies within $a1 yds for $d.', 'EffectBonusMultiplier_1': 0.19300000369548798, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 4096, 'SpellClassSet': 5, 'SpellLevel': 40, 'SpellPriority': 50, 'SpellVisualID_1': 7732, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 500, 'Targets': 64},
)
scripted_by(shadowfury_30283, 'spell_warl_fury_of_the_void')


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
    raw_overrides={'AttributesEx3': 67108992, 'AttributesEx5': 32, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage taken from Shadow damage-over-time effects increased by $s3%.', 'BaseLevel': 60, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You send a ghostly soul into the target, dealing $s1 Shadow damage and increasing all damage done by your Shadow damage-over-time effects on the target by $s3% for $d. When the Haunt spell ends or is dispelled, the soul returns to you, healing you for $s2% of the damage it did to the target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskC_1': m.SHADOW_PERIODIC[0], 'EffectSpellClassMaskC_2': m.SHADOW_PERIODIC[1], 'EffectSpellClassMaskC_3': m.SHADOW_PERIODIC[2], 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 20.0, 'SpellClassMask_2': 262144, 'SpellClassSet': 5, 'SpellLevel': 60, 'SpellVisualID_1': 10731, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
scripted_by(haunt_48181, 'spell_warl_haunt_soulburn')


chaos_bolt_50796 = spell(
    id=50796,
    name='Chaos Bolt',
    school=36,  # School.FIRE | School.SHADOW (Shadowflame, DESTRUCTION §0.2.5)
    attributes=65536,
    category=1225,
    cast_time_ms=2500,
    cooldown_ms=0,
    category_cooldown_ms=12000,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=557, points_per_level=13.95, die_sides=225, implicit_target_a=6),
    ],
    spell_icon_id=3178,
    notes="warlock-rework DESTRUCTION §4.1 (B3 rebase, moved (10,1)->(6,1), learn level 60->40): bp/ppl rescaled so the level-60 value is unchanged (558-782 @40, 837-1061 @60, 1116-1340 @80, -22% vs todays @80); coefficient/cast_time_ms/mana_cost_pct unchanged. School Fire (4) -> 36 (Fire|Shadow, Shadowflame per §0.2.5; crit still reads GetFirstSchoolInMask=Fire, unchanged). Description names Chaotic Burn and Soulburn: Chaos Bolt/Soul Fire (§6.1); Mastery capstone is spell_warl_chaos_bolt_mastery (WP-B).",
    raw_overrides={'AttributesEx3': 262144, 'AttributesEx4': 2048, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 40, 'CastingTimeIndex': 19, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Sends a bolt of chaotic fire at the enemy, dealing $s1 Shadowflame damage and leaving Chaotic Burn on the target. Chaos Bolt cannot be resisted, and pierces through all absorption effects. Learning Chaos Bolt also grants Soulburn: Chaos Bolt and Soulburn: Soul Fire.\n\nChaotic Burn: deals 25% of Chaos Bolt's damage as Shadowflame damage over 6 sec, ticking every 2 sec. Your Conflagrate deals 20% more damage to targets afflicted by your Chaotic Burn.\n\nCapstone Bonus: Chaos Bolt's damage is increased by your Mastery.", 'EffectBonusMultiplier_1': 0.7139999866485596, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 20.0, 'SpellClassMask_2': 131072, 'SpellClassSet': 5, 'SpellLevel': 40, 'SpellVisualID_1': 11240, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
scripted_by(chaos_bolt_50796, 'spell_warl_chaos_bolt', 'spell_warl_chaos_bolt_mastery')


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
    notes='warlock-rework DESTRUCTION §0.1.2/§6/§9 (C12 made inert): TargetAuraState 14->0 (client patch too) removes the stock consume-branch and its CheckTarget requirement; spell_warl_conflagrate (WP-B) rewrites the damage entirely from live Immolate/Shadowflame snapshots (§7.3). EffectBasePoints_3 39->84 (the 85% periodic share, raw $s3 stat used only for tooltip substitution - the actual per-tick amount is set by the script via SetSpellValue).',
    raw_overrides={'AttributesEx': 131072, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Fire damage every $t2 seconds.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Consumes an Immolate or Shadowflame effect on the enemy target to instantly deal damage equal to 100% of your Immolate or Shadowflame, and causes an additional 85% damage over $d.\n\nCapstone Bonus: Conflagrate\'s direct and periodic damage is increased by your Mastery.', 'EffectBasePoints_3': 84, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 8388608, 'SpellClassSet': 5, 'SpellLevel': 1, 'SpellVisualID_1': 5199, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetAuraState': 0},
)
scripted_by(conflagrate_17962, 'spell_warl_conflagrate')


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
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=6, apply_aura=AuraType.MOD_DECREASE_SPEED),
    ],
    spell_icon_id=228,
    notes='warlock-rework AFFLICTION §4.5 B14 / §4.7 B19: now an ordinary curse (B14 - no longer bane-adjacent), slow raised to 50% (spec §5.2), baseline learn level 20 with trainer 214',
    raw_overrides={'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement speed slowed by $s1%.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces the target's movement speed by $s1% for $d.  Only one Curse per Warlock can be active on any one target.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 4194304, 'SpellClassSet': 5, 'SpellLevel': 20, 'SpellVisualID_1': 8785, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
trained_by(curse_of_exhaustion_18223, trainer_id=214, req_level=20, money_cost=2000)
skill_line_ability(id=10296, skill_line=355, spell_id=18223, class_mask=256)


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
trained_by(fel_domination_18708, trainer_id=214, req_level=20, money_cost=2000)
skill_line_ability(id=10531, skill_line=354, spell_id=18708, class_mask=256, min_skill_line_rank=1)


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
    notes='warlock-rework DEMONOLOGY §4.5: talent -> baseline at 20 (BaseLevel/SpellLevel already 20 from stock, no data change there). trained_by/skill_line_ability(11196 override) added below; tooltip updated to drop the per-demon list and "cannot be prevented" clause (B14-era wording no longer applies) per §4.5.',
    raw_overrides={'AttributesEx2': 4, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When active, 20% of all damage taken by the caster is taken by your summoned or enslaved demon instead. Lasts as long as the demon is active and controlled.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_3': 64, 'SpellClassSet': 5, 'SpellLevel': 20, 'SpellVisualID_1': 969, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetCreatureType': 4},
)
trained_by(soul_link_19028, 214, 20, 2000)
skill_line_ability(id=11196, skill_line=354, spell_id=19028, class_mask=256)
scripted_by(25228, 'spell_warl_soul_link_split')


metamorphosis_47241 = spell(
    id=47241,
    name='Metamorphosis',
    school=School.NORMAL,
    attributes=16,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MOD_SHAPESHIFT, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=149, implicit_target_a=1, apply_aura=AuraType.MOD_BASE_RESISTANCE_PCT, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=127),
    ],
    spell_icon_id=3314,
    notes="warlock-rework DEMONOLOGY §5.2: duration 30000 -> 20000; eff1 armor 599 -> 149 (+150%); eff2 damage 19 -> 14 (+15%; Demonic Form's +2/4/6% is added to this effect's live amount by spell_warl_metamorphosis_demo's DoEffectCalcAmount EFFECT_2, §7.13); ShapeshiftExclude |= 0x400000 (form 23 Dark Apotheosis's stance bit) so Metamorphosis can't be cast while in Dark Apotheosis (enforced here because 200836's aura-275 mask deliberately leaves out 47241's own d3 0x2000 bit, §0.2.3). linked to 200837 (SB instant/Demonic Form/Nemesis capstone) and 200838 (Demonic Bulwark form) below.",
    raw_overrides={'AttributesEx': 131072, 'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 67108864, 'EffectSpellClassMaskB_2': 16384, 'SpellVisualID_1': 12118, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': "You transform into a Demon for $d. While transformed, your Shadow Bolt is instant and extends your Bane of Doom on the target by 3 sec, to at most 30 sec remaining, and your Hand of Gul'dan also damages all other enemies within 8 yards of the target. You may use Immolation Aura and Demonic Leap, and all of your other warlock spells remain usable. Increases your armor from cloth and leather items by $47241s2% and your damage by $47241s3%, reduces the chance you are critically hit by melee attacks by 6%, and reduces the duration of stun and snare effects by $54817s1%. Your demons deal 15% more damage while you are transformed. Cannot be used with Dark Apotheosis.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Demon Form.\nArmor contribution from items increased by $47241s2%.\nChance to be critically hit by melee reduced by 6%.\nDamage increased by $47241s3%.\nStun and snare duration reduced by $54817s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 5, 'SpellClassMask_3': 8192, 'ShapeshiftExclude': 4194304, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0},
)
scripted_by(metamorphosis_47241, 'spell_warl_metamorphosis_demo')
linked_spell(47241, 200837, type=2)
linked_spell(47241, 200838, type=2)


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
    notes='warlock-rework DEMONOLOGY §6 (2,1): BaseLevel/SpellLevel 50 -> 20 (B3, no scaling values to change).',
    raw_overrides={'AttributesEx': 131073, 'AttributesEx5': 2, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Felguard under the command of the Warlock.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Summon', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'ReagentCount_1': 0, 'Reagent_1': 0, 'SpellClassMask_1': 536870912, 'SpellClassSet': 5, 'SpellLevel': 20, 'SpellVisualID_1': 8360, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


demonic_empowerment_47193 = spell(
    id=47193,
    name='Demonic Empowerment',
    school=School.SHADOW,
    attributes=537135104,
    cast_time_ms=0,
    cooldown_ms=45000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=100.0,
    effects=[
        Effect(type=77, base_points=-1, implicit_target_a=5),
    ],
    spell_icon_id=3174,
    notes='warlock-rework DEMONOLOGY §6 (8,1): moved (6,1)->(8,1). cooldown_ms 60000 -> 45000 (>=30s -> Cooldown Haste eligible). attributes: dropped NOT_SHAPESHIFTED (0x10000) so it is usable in Metamorphosis/Dark Apotheosis (§11 Q2). cost 6% kept; SpellLevel 30 kept. Voidwalker +20% health needs the custom BP (spell_warl_demonic_empowerment_demo, §7.10); 54443/54508 unchanged (stock 20s/15s already match, §5.3).',
    raw_overrides={'AttributesEx2': 4, 'AttributesEx3': 1073741824, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Empowered.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Empowers your summoned demon and sacrifices up to 2 of your Wild Imps, granting you one Molten Core for each. Voidwalker: Health and threat generation increased by 20% for 20 sec. Felguard: Attack speed increased by 20% for 15 sec, removes all stun, snare and movement impairing effects, and grants immunity to them for the duration.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'SpellClassMask_3': 4160, 'SpellClassSet': 5, 'SpellLevel': 30, 'SpellVisualID_1': 13422, 'TargetCreatureType': 4},
)
scripted_by(demonic_empowerment_47193, 'spell_warl_demonic_empowerment_demo')
unbind_script(47193, 'spell_warl_demonic_empowerment')



summon_felhunter_691 = spell(
    id=691,
    name='Summon Felhunter',
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
        Effect(type=56, implicit_target_a=32, misc_value=417),
    ],
    spell_icon_id=214,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131073, 'AttributesEx5': 2, 'CastingTimeIndex': 7, 'InterruptFlags': 15, 'ProcChance': 101, 'BaseLevel': 30, 'SpellLevel': 30, 'RangeIndex': 1, 'Reagent_1': 0, 'ReagentCount_1': 0, 'EquippedItemClass': -1, 'SpellVisualID_1': 7313, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Summon', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Felhunter under the command of the Warlock.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'SpellClassSet': 5, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


summon_voidwalker_697 = spell(
    id=697,
    name='Summon Voidwalker',
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
        Effect(type=56, implicit_target_a=32, misc_value=1860),
    ],
    spell_icon_id=217,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131073, 'AttributesEx5': 2, 'CastingTimeIndex': 7, 'InterruptFlags': 15, 'ProcChance': 101, 'BaseLevel': 10, 'SpellLevel': 10, 'RangeIndex': 1, 'Reagent_1': 0, 'ReagentCount_1': 0, 'EquippedItemClass': -1, 'SpellVisualID_1': 4054, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Summon', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Voidwalker under the command of the Warlock.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'SpellClassSet': 5, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


summon_succubus_712 = spell(
    id=712,
    name='Summon Succubus',
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
        Effect(type=56, implicit_target_a=32, misc_value=1863),
    ],
    spell_icon_id=216,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131073, 'AttributesEx5': 2, 'CastingTimeIndex': 7, 'InterruptFlags': 15, 'ProcChance': 101, 'BaseLevel': 20, 'SpellLevel': 20, 'RangeIndex': 1, 'Reagent_1': 0, 'ReagentCount_1': 0, 'EquippedItemClass': -1, 'SpellVisualID_1': 4055, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Summon', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Succubus under the command of the Warlock.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'SpellClassSet': 5, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


summon_voidwalker_25112 = spell(
    id=25112,
    name='Summon Voidwalker',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=10000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=56, implicit_target_a=32, misc_value=1860),
    ],
    spell_icon_id=217,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131073, 'CastingTimeIndex': 7, 'InterruptFlags': 15, 'ProcChance': 101, 'BaseLevel': 10, 'SpellLevel': 10, 'RangeIndex': 1, 'Reagent_1': 0, 'ReagentCount_1': 0, 'EquippedItemClass': -1, 'SpellVisualID_1': 4054, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Summon', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Casts your Summon Voidwalker spell with no mana requirement.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'SpellClassSet': 5, 'SpellClassMask_1': 536870912, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


ritual_of_summoning_61993 = spell(
    id=61993,
    name='Ritual of Summoning',
    school=School.SHADOW,
    attributes=268435456,
    cast_time_ms=5000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=12,
    range_yards=30.0,
    duration_ms=300000,
    effects=[
        Effect(type=50, die_sides=0, implicit_target_a=47, misc_value=194097, radius_yards=0.0),
    ],
    spell_icon_id=164,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'CastingTimeIndex': 6, 'InterruptFlags': 15, 'ChannelInterruptFlags': 15374, 'ProcChance': 101, 'BaseLevel': 20, 'SpellLevel': 20, 'Reagent_1': 0, 'ReagentCount_1': 0, 'EquippedItemClass': -1, 'EffectRadiusIndex_1': 36, 'SpellVisualID_1': 1523, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Begins a ritual that creates a summoning portal.  The summoning portal can be used by 2 party or raid members to summon a targeted party or raid member.  The ritual portal requires the caster and 2 additional party or raid members to complete.  In order to participate, all players must be out of combat and right-click the portal and not move until the ritual is complete.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'SpellClassSet': 5, 'SpellClassMask_3': 64, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


create_healthstone_11729 = spell(
    id=11729,
    name='Create Healthstone',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=53,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.SCRIPT_EFFECT, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=284,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx5': 2, 'CastingTimeIndex': 14, 'InterruptFlags': 15, 'ProcChance': 101, 'BaseLevel': 46, 'SpellLevel': 46, 'RangeIndex': 1, 'Reagent_1': 0, 'Reagent_2': -2, 'ReagentCount_1': 0, 'ReagentCount_2': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 138, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Creates a Greater Healthstone that can be used to instantly restore $5723s1 health.\n\nConjured items disappear if logged out for more than 15 minutes.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'SpellClassSet': 5, 'SpellClassMask_1': 1048576, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0},
)


create_healthstone_28023 = spell(
    id=28023,
    name='Create Healthstone',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=95,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.SCRIPT_EFFECT, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=284,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268566528, 'AttributesEx5': 2, 'CastingTimeIndex': 14, 'InterruptFlags': 15, 'ProcChance': 101, 'BaseLevel': 10, 'SpellLevel': 10, 'RangeIndex': 1, 'Reagent_1': 0, 'ReagentCount_1': 0, 'EquippedItemClass': -1, 'SpellVisualID_1': 138, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Creates a Minor Healthstone that can be used to instantly restore $6262s1 health.\n\nConjured items disappear if logged out for more than 15 minutes.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'SpellClassSet': 5, 'SpellClassMask_1': 1048576, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0},
)


soulshatter_29858 = spell(
    id=29858,
    name='Soulshatter',
    school=School.SHADOW,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    power_type=PowerType.HEALTH,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=-51, implicit_target_a=22, implicit_target_b=15, radius_yards=50.0),
    ],
    spell_icon_id=1954,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx3': 393216, 'AttributesEx4': 65536, 'AttributesEx5': 2, 'CastingTimeIndex': 1, 'InterruptFlags': 8, 'ProcChance': 101, 'MaxLevel': 72, 'BaseLevel': 66, 'SpellLevel': 66, 'DurationIndex': 0, 'RangeIndex': 1, 'Speed': 22.0, 'Reagent_1': 0, 'ReagentCount_1': 0, 'EquippedItemClass': -1, 'SpellVisualID_1': 7687, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces threat by $s1% for all enemies within $a1 yards.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


spell_lock_19647 = spell(
    id=19647,
    name='Spell Lock',
    school=School.SHADOW,
    attributes=262144,
    category=88,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=24000,
    mana_cost=200,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.INTERRUPT_CAST, base_points=-1, mechanic=26, implicit_target_a=6),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, mechanic=Mechanic.SILENCE, implicit_target_a=6, trigger_spell=24259),
    ],
    spell_icon_id=77,
    notes='pulled from existing data; warlock-rework classmask-scope-audit Bug B: added SpellClassMask_3=SPELL_LOCK (stock row shipped with no family flag, so Improved Felhunter\'s "and Spell Lock" cooldown clause matched nothing)',
    raw_overrides={'CastingTimeIndex': 1, 'InterruptFlags': 8, 'ProcChance': 101, 'BaseLevel': 52, 'SpellLevel': 52, 'EquippedItemClass': -1, 'SpellVisualID_1': 5282, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': "Silences the enemy for $24259d.  If used on a casting target, it will counter the enemy's spellcast, preventing any spell from that school of magic from being cast for $d.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassMask_3': m.SPELL_LOCK, 'SpellClassSet': 5, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


# ---------------------------------------------------------------------------
# warlock-rework AFFLICTION pass - new player-castable spells (§5). Shared
# ids 200710/200709 (buff)/200711/200712 declared here or in
# warlock_trigger_spells.py per which one is player-cast (SHARED §1.3).
# ---------------------------------------------------------------------------

soulburn_200710 = spell(
    id=200710,
    name='Soulburn',
    school=School.SHADOW,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=5000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=RANGE_SELF,
    effects=[
        Effect(type=EffectType.TRIGGER_SPELL, implicit_target_a=1, trigger_spell=200711),
    ],
    spell_icon_id=90155,
    notes='warlock-rework AFFLICTION §5/§7.11 (SHARED §1.3, PLAN B10): baseline for every warlock, learn level 12, 5s cooldown, off the GCD (StartRecoveryCategory/Time 0), castable while another cast/channel is in progress (AttributesEx4 0x80 ALLOW_CAST_WHILE_CASTING), usable while shapeshifted (no NOT_SHAPESHIFTED, so attributes=0 rather than the usual 65536), consumes 1 Soul Shard (script-enforced, no reagent). Data only - Warlock::TryConsumeSoulburnMarker/CheckCast are WP-B.',
    raw_overrides={'AttributesEx4': 128, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 12, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Consumes a Soul Shard, empowering your next Seed of Corruption or Haunt for 20 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 5, 'SpellLevel': 12, 'SpellPriority': 50, 'SpellVisualID_1': 816, 'StartRecoveryCategory': 0, 'StartRecoveryTime': 0},
)
trained_by(soulburn_200710, trainer_id=214, req_level=12, money_cost=600)
skill_line_ability(id=30456, skill_line=355, spell_id=soulburn_200710.id, class_mask=256)
scripted_by(soulburn_200710, 'spell_warl_soulburn')


phantom_singularity_200729 = spell(
    id=200729,
    name='Phantom Singularity',
    school=School.SHADOW,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=50000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=30.0,
    duration_ms=16000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DUMMY, implicit_target_a=6, amplitude=2000),
    ],
    spell_icon_id=173,
    notes='warlock-rework AFFLICTION §5/§6 (4,1 - talent 1081, repurposed Curse of Exhaustion cell), §7.17: PERIODIC_DUMMY debuff that recasts the damage spell (200730) at the target every 2s; hasted (AttributesEx5 0x2000 SPELL_HASTE_AFFECTS_PERIODIC - not hasted by default); SpellClassMask_3 carries PHANTOM_SINGULARITY_CAST so both Reach passives extend its range (§11 Q17); no NOT_SHAPESHIFTED (usable in Metamorphosis, DEMONOLOGY §11 Q2). Cooldown Haste eligible (>=30s base, QA #47).',
    raw_overrides={'AttributesEx5': 8192, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 30, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Places a phantom singularity above the target, dealing $200730s1 Shadow damage every $t1 sec to the target and all enemies within 10 yards of it for $d. You are healed for 20% of all damage it deals.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_3': 0x00200000, 'SpellClassSet': 5, 'SpellLevel': 30, 'SpellVisualID_1': 8339, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
scripted_by(phantom_singularity_200729, 'spell_warl_phantom_singularity')


dark_soul_misery_200732 = spell(
    id=200732,
    name='Dark Soul: Misery',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=RANGE_SELF,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL),
    ],
    spell_icon_id=90154,
    notes='warlock-rework AFFLICTION §5/§6 (8,1 - talent 60074): off the GCD (§11 Q11, user), Cooldown Haste eligible (>=30s base). Data only.',
    raw_overrides={'AttributesEx5': 8192, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Haste increased by $s1%.', 'BaseLevel': 50, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your haste by $s1% for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 5, 'SpellLevel': 50, 'SpellVisualID_1': 8339, 'StartRecoveryCategory': 0, 'StartRecoveryTime': 0},
)


soul_swap_200733 = spell(
    id=200733,
    name='Soul Swap',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.DUMMY, implicit_target_a=6),
    ],
    spell_icon_id=90150,
    notes='warlock-rework AFFLICTION §5/§6/§7.9: baseline learn level 40, no cooldown, on the GCD; copies Corruption/Bane of Agony/Unstable Affliction from the target (default answer, §11 Q3). Data only - C++ in spell_warl_soul_swap.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 40, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Copies your Corruption, Bane of Agony and Unstable Affliction from the target, preserving their power and duration. For 10 sec afterwards, the next target you cast Soul Swap: Exhale on is afflicted by the copied effects. Cannot Soul Swap to the same target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 5, 'SpellLevel': 40, 'SpellVisualID_1': 8339, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
trained_by(soul_swap_200733, trainer_id=214, req_level=40, money_cost=11000)
skill_line_ability(id=30466, skill_line=355, spell_id=soul_swap_200733.id, class_mask=256)
scripted_by(soul_swap_200733, 'spell_warl_soul_swap')


soul_swap_exhale_200734 = spell(
    id=200734,
    name='Soul Swap: Exhale',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.DUMMY, implicit_target_a=6),
    ],
    spell_icon_id=2028,
    notes='warlock-rework AFFLICTION §5/§6/§7.9: baseline learn level 40, no cost, on the GCD; CasterAuraSpell=200735 greys the button out client-side without the copy. Data only - C++ in spell_warl_soul_swap_exhale.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 40, 'CasterAuraSpell': 200735, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Afflicts the target with the effects copied by Soul Swap.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 5, 'SpellLevel': 40, 'SpellVisualID_1': 8339, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
trained_by(soul_swap_exhale_200734, trainer_id=214, req_level=40, money_cost=11000)
skill_line_ability(id=30467, skill_line=355, spell_id=soul_swap_exhale_200734.id, class_mask=256)
scripted_by(soul_swap_exhale_200734, 'spell_warl_soul_swap_exhale')


soul_harvest_200736 = spell(
    id=200736,
    name='Soul Harvest',
    school=School.SHADOW,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=RANGE_SELF,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=126),
    ],
    spell_icon_id=90152,
    notes='warlock-rework AFFLICTION §5/§6/§7.19: baseline learn level 60, off the GCD (§11 Q11, user); duration set by script (§7.19) up to a max of 24s; joins stock group 1107 "Temporary Damage Increases" for its does-not-stack rule (§11 Q12, no new group id). Self-cast only: the pet half is the separate aura 200737 applied by the script when a pet exists (a TARGET_UNIT_PET effect here made the cast fail with no pet / pet out of range - playtest 2026-09-28).',
    raw_overrides={'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Magic damage increased by $s1%.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Consumes the lingering souls of nearby enemies you are fighting, increasing your and your pet's magic damage done by 15% for up to 24 sec, based on the number of enemies affected by your Corruption, Bane of Agony, Unstable Affliction, Shadow Word: Pain or Devouring Plague.", 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 5, 'SpellLevel': 60, 'SpellVisualID_1': 7963, 'StartRecoveryCategory': 0, 'StartRecoveryTime': 0},
)
trained_by(soul_harvest_200736, trainer_id=214, req_level=60, money_cost=26000)
skill_line_ability(id=30468, skill_line=355, spell_id=soul_harvest_200736.id, class_mask=256)
scripted_by(soul_harvest_200736, 'spell_warl_soul_harvest')
spell_group(1107, soul_harvest_200736)


burning_rush_200738 = spell(
    id=200738,
    name='Burning Rush',
    school=School.FIRE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.PERIODIC_DAMAGE_PERCENT, amplitude=2000),
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=AuraType.MOD_INCREASE_SPEED),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.MOD_MINIMUM_SPEED),
    ],
    spell_icon_id=90153,
    notes='warlock-rework AFFLICTION §5/§6/§7.19 (PLAN B12): toggle - baseline learn level 20; self-damage does not break CC (AttributesEx4 0x4000 DAMAGE_DOESNT_BREAK_AURAS) and cannot crit (AttributesEx2 0x20000000); self-damage suppresses casterprocs (AttributesEx3 0x10000); right-click cancellable via custom_attr below. No cast-while-moving (B12 dropped that clause). SpellVisualID_1 5926 -> 90026: the speed ribbon of stock SV 5926 plus a StateKit of flames at the feet while toggled on (patch_warlock_vfx_models.py).',
    raw_overrides={'AttributesEx2': 536870912, 'AttributesEx3': 65536, 'AttributesEx4': 16384, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Draining health to move faster.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Drains 5% of your maximum health every 2 sec to increase your movement speed by 50%. This damage does not break crowd control, and movement impairing effects may not reduce you below 100% normal speed. Cast again to cancel.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 5, 'SpellLevel': 20, 'SpellVisualID_1': 90026, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
trained_by(burning_rush_200738, trainer_id=214, req_level=20, money_cost=2000)
skill_line_ability(id=30469, skill_line=354, spell_id=burning_rush_200738.id, class_mask=256)
scripted_by(burning_rush_200738, 'spell_warl_burning_rush')
custom_attr(burning_rush_200738, attributes=0x0E000000)


# ---------------------------------------------------------------------------
# warlock-rework DESTRUCTION pass (S2) - new player-castable spells (§5,
# DESTRUCTION.md §2.1). Talent grants (granted_by_talent, SLA rows) are in
# warlock_talents.py.
# ---------------------------------------------------------------------------

havoc_200974 = spell(
    id=200974,
    name='Havoc',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=40.0,
    duration_ms=60000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, die_sides=1, implicit_target_a=6, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=90172,
    notes='warlock-rework DESTRUCTION §5 (8,1) NEW talent 60102, level 50: single-target debuff - AttributesEx5 |= 0x20 (SPELL_ATTR5_LIMIT_N, one Havoc per caster, a new target removes the old - Mass Entanglement bugs-and-fixes precedent). SpellClassMask_3 = HAVOC (§2.4 - only mattered for the old narrow Metamorphosis mask, now harmless since that mask is full). Duplication itself is spell_warl_chaos_bolt (WP-B, §7.5); the Rift AI also duplicates Rift Bolts onto the Havoc target (§7.2). SpellVisualID_1 8761 = stock Felfire Proc: the Chaos Bolt fel hand Precast/Cast kits 7085/7086 + fel burst on the target head, no missile.',
    raw_overrides={'AttributesEx5': 32, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': "Your enemy's Chaos Bolts also strike this target.", 'BaseLevel': 50, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Marks an enemy with Havoc for $d. Your Chaos Bolts cast at another enemy also strike the Havoc target. Only one Havoc can be active at a time.', 'EffectChainAmplitude_1': 1.0, 'SpellVisualID_1': 8761, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_3': m.HAVOC, 'SpellClassSet': 5, 'SpellLevel': 50, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


chaos_rift_200978 = spell(
    id=200978,
    name='Chaos Rift',
    school=School.SHADOW,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=90000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=RANGE_SELF,
    effects=[
        Effect(type=77, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=90171,
    notes='warlock-rework DESTRUCTION §5 (10,1) NEW talent 60104, level 60: SCRIPT_EFFECT summons creature 300170 beside the caster (spell_warl_chaos_rift, WP-B, §7.2). SpellClassMask_3 = CHAOS_RIFT (§2.4, harmless). Cooldown Haste eligible (>=30s base rule, PLAN §3.12). SpellVisualID_1 10677 = stock Demonic Circle: Summon (Shadow Uber hand Precast/Cast, omni).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Tears open a Chaos Rift beside you for 12 sec. Every 2 sec, the Rift fires a Chaos Bolt at a viable enemy for 50% of Chaos Bolt's damage.", 'EffectChainAmplitude_1': 1.0, 'SpellVisualID_1': 10677, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_3': m.CHAOS_RIFT, 'SpellClassSet': 5, 'SpellLevel': 60, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
scripted_by(chaos_rift_200978, 'spell_warl_chaos_rift')


# creature_template/creature_template_model (stage T1 DSL helpers, DESTRUCTION.md §0.5 Q12/§2.6) -
# Chaos Rift 300170, no hand-written pending_db_world SQL. Display 11686 (InvisibleStalker, model
# scale 1.0): the portal is not the body but the stock "Open Portal" aura 45977 the AI puts on it,
# whose StateKit plays SPELLS\Creature_SpellPortal_LargeShadow at effect scale 0.5 - the way
# Jaraxxus's Nether Portal 34825 (stalker + aura 66263) and every other stock user shows that model.
# Worn as a display (27735) the model looped its Stand opening; a StateKit plays it once, then Hold.
# scale 0.6 x 0.5 = 0.3, what the user asked for as "0.1" on 27735's 3.0 display scale (playtest
# 2026-09-29). unit_flags 33554434
# (NOT_SELECTABLE | NON_ATTACKABLE, Tentacle of Madness 300102 precedent); flags_extra 66 (no
# TRIGGER bit - that flag makes a creature invisible, bugs-and-fixes); faction 35 and level 1 in
# the template, overwritten by the owner's own faction/level at summon (npc_warl_chaos_rift,
# WP-B); type 10 (not a demon, so no talent affecting demons touches it).
creature_template(
    300170, 'Chaos Rift',
    minlevel=1, maxlevel=1,
    faction=35,
    unit_flags=33554434,
    unit_flags2=2048,
    type=10,
    flags_extra=66,
    ScriptName='npc_warl_chaos_rift',
)
creature_model(300170, display_id=11686, scale=0.6)


immolation_aura_50589 = spell(
    id=50589,
    name='Immolation Aura',
    school=School.FIRE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=64,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=1000, trigger_spell=50590),
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=16),
    ],
    spell_icon_id=937,
    notes='warlock-rework DEMONOLOGY §5.2: ShapeshiftMask 0x200000 -> 0x600000 (Metamorphosis + Dark Apotheosis, form 22 | form 23 bits); BaseLevel/SpellLevel 60 -> 10 (B3). Cost/30s CD/15s duration kept. AttributesEx5 0x2000 kept (haste adds pulses). Tick 50590 edited separately in warlock_trigger_spells.py (§4.0/§7.13).',
    raw_overrides={'AttributesEx': 98304, 'AttributesEx5': 8192, 'ShapeshiftMask': 6291456, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31788, 'ProcChance': 101, 'BaseLevel': 10, 'SpellLevel': 10, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectDieSides_2': 1, 'EffectBasePoints_2': -1, 'SpellVisualID_1': 12038, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Demon', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Ignites the area surrounds you, causing $50590s1 Fire damage to all nearby enemies every $50589t1 sec.  Lasts $50589d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damages all nearby enemies.', 'AuraDescription_Lang_Mask': 16712190, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'SpellClassSet': 5, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0},
)
linked_spell(-200835, -50589, type=0)


challenging_howl_59671 = spell(
    id=59671,
    name='Challenging Howl',
    school=School.NORMAL,
    mechanic=16,
    attributes=65552,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    power_type=PowerType.RAGE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=22, implicit_target_b=15, apply_aura=AuraType.MOD_TAUNT, radius_yards=10.0),
        Effect(type=114, die_sides=0, implicit_target_a=22, implicit_target_b=15, radius_yards=10.0),
    ],
    spell_icon_id=2024,
    notes='warlock-rework DEMONOLOGY §5.2: ShapeshiftMask 0x200000 -> 0x400000 (Dark Apotheosis only, form 23 bit); cooldown_ms 15000 -> 180000; 10 yd / 6 s kept.',
    raw_overrides={'AttributesEx2': 67108864, 'AttributesEx4': 2048, 'AttributesEx6': 8388608, 'ShapeshiftMask': 4194304, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 1, 'SpellLevel': 1, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 209, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Demon', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Taunts all enemies within $a1 yards for $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Taunted.', 'AuraDescription_Lang_Mask': 16712190, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'SpellClassSet': 5, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


demon_charge_54785 = spell(
    id=54785,
    name='Demon Charge',
    school=School.NORMAL,
    attributes=327696,
    category=1219,
    cast_time_ms=0,
    cooldown_ms=25000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=25.0,
    effects=[
        Effect(type=EffectType.CHARGE, die_sides=0, implicit_target_a=6),
        Effect(type=EffectType.TRIGGER_SPELL, base_points=-1, implicit_target_a=6, trigger_spell=60995),
    ],
    spell_icon_id=129,
    notes='warlock-rework DEMONOLOGY §5.2: ShapeshiftMask 0x200000 -> 0x400000 (Dark Apotheosis only); RecoveryTime (cooldown_ms) 45000 -> 25000; RangeIndex 95 (8-25 yd) kept; BaseLevel/SpellLevel 60 -> 10.',
    raw_overrides={'AttributesEx': 32768, 'AttributesEx6': 8389696, 'AttributesEx7': 262144, 'ShapeshiftMask': 4194304, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 10, 'SpellLevel': 10, 'DurationIndex': 0, 'RangeIndex': 95, 'EquippedItemClass': -1, 'EffectDieSides_3': 1, 'EffectBasePoints_3': -1, 'SpellVisualID_1': 29, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Demon', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Charge an enemy, stunning it for $60995d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'DefenseType': 1, 'PreventionType': 2, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


demonic_leap_54786 = spell(
    id=54786,
    name='Demonic Leap',
    school=School.SHADOW,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    range_yards=25.0,
    duration_ms=2000,
    effects=[
        Effect(type=42, implicit_target_a=87, misc_value=50),
    ],
    spell_icon_id=129,
    notes="warlock-rework DEMONOLOGY §4.7 (B11): stock Demon Leap 54786 retuned into 'Demonic Leap' - eff0 stun+eff1 damage removed, replaced by a single JUMP_DEST (42) effect, implicit_target_a=87 (DEST_DEST), misc_value=50 (min arc 5 yd, Spell::CalculateJumpSpeeds). SpellClassSet 5 / SpellClassMask_3 = DEMONIC_LEAP (Nemesis). Stances 0x200000 (Metamorphosis only). Category/CategoryRecoveryTime 44/45000 -> 0/0; cooldown_ms 30000 (>=30s -> Cooldown Haste eligible). No cost (power_type dropped). BaseLevel/SpellLevel 60 -> 40 (Metamorphosis row 6). SLA 30481 (stock 54786 had none).",
    raw_overrides={'AttributesEx2': 4, 'Targets': 64, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 40, 'SpellLevel': 40, 'Speed': 28.0, 'EquippedItemClass': -1, 'SpellVisualID_1': 12033, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'Leap to the target location. Metamorphosis only.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'DefenseType': 1, 'PreventionType': 2, 'ShapeshiftMask': 2097152, 'SpellClassSet': 5, 'SpellClassMask_3': m.DEMONIC_LEAP, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)
skill_line_ability(id=30481, skill_line=354, spell_id=54786, class_mask=256)


dark_apotheosis_200835 = spell(
    id=200835,
    name='Dark Apotheosis',
    school=School.NORMAL,
    attributes=16,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MOD_SHAPESHIFT, misc_value=23),
        Effect(type=EffectType.APPLY_AURA, base_points=199, implicit_target_a=1, apply_aura=AuraType.MOD_BASE_RESISTANCE_PCT, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=299, implicit_target_a=1, apply_aura=AuraType.MOD_THREAT, misc_value=127),
    ],
    spell_icon_id=90162,
    notes='warlock-rework DEMONOLOGY §5.2: toggle form (form 23), learned by talent learner 200863. SpellVisualID_1 12118 = the transform burst of Metamorphosis 47241 (metamorphosis.mdx); the demon model itself comes from shapeshift_form(23) below. ShapeshiftExclude=0x200000 (form 22 Metamorphosis bit - cannot be cast while in Metamorphosis, §11 Q22). linked to 200836 (passive), 200838 (Demonic Bulwark form) and crit-immunity 200000, all type 2; the Immolation Aura twin-removal link (-200835 -> -50589) is declared on 50589 itself above.',
    raw_overrides={'AttributesEx': 131072, 'ShapeshiftExclude': 2097152, 'SpellVisualID_1': 12118, 'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shifts you into a demonic form until cancelled. While in this form you are immune to critical strikes from melee and ranged attacks, your armor from cloth and leather items is increased by $s2%, your threat generation is increased by $s3%, and your damage done is reduced by 20%. Grants Immolation Aura, Demon Charge, Demonic Taunt and Challenging Howl. Cannot be used with Metamorphosis.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Demonic form. Immune to critical strikes. Armor and threat increased, damage done reduced.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 0, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)
scripted_by(dark_apotheosis_200835, 'spell_warl_dark_apotheosis')
skill_line_ability(id=30475, skill_line=354, spell_id=200835, class_mask=256)
linked_spell(200835, 200836, type=2)
linked_spell(200835, 200838, type=2)
linked_spell(200835, 200000, type=2)


implosion_200827 = spell(
    id=200827,
    name='Implosion',
    school=School.SHADOW | School.FIRE,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=6000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.DUMMY, implicit_target_a=6),
    ],
    spell_icon_id=2356,
    notes="warlock-rework DEMONOLOGY §6 (4,0): rank spell of new talent 1281 (repurposed from Mana Feed, same cell). CheckCast fails with no Wild Imps (spell_warl_implosion). eff0 DUMMY is the OnHit trigger marker read by the script (imps leap and explode, §7.2/§7.3). No NOT_SHAPESHIFTED (usable in Metamorphosis/Dark Apotheosis). SpellClassSet 5, no family bits (nothing needs to scope a modifier onto it).",
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Commands all of your Wild Imps to leap at the target and explode, each dealing $200828s1 Shadowflame damage to all enemies within 8 yards. The damage of each imp does not depend on its remaining energy. Implosion counts as damage done by your demons.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 5, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'DefenseType': 1, 'PreventionType': 1, 'InterruptFlags': 15, 'FacingCasterFlags': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)
scripted_by(implosion_200827, 'spell_warl_implosion')


call_dreadstalkers_200829 = spell(
    id=200829,
    name='Call Dreadstalkers',
    school=School.SHADOW,
    attributes=0,
    cast_time_ms=2000,
    cooldown_ms=20000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=40.0,
    duration_ms=13000,
    effects=[
        Effect(type=EffectType.SUMMON, implicit_target_a=32, misc_value=300152),
        Effect(type=EffectType.SUMMON, implicit_target_a=32, misc_value=300152),
        Effect(type=EffectType.DUMMY, implicit_target_a=6),
    ],
    spell_icon_id=4062,
    notes='warlock-rework DEMONOLOGY §5.1/§6 (4,1): rank spell of new talent 60083. Two SUMMON effects (props 1021 always summons exactly 1 per effect, SpellEffects.cpp:2501-2522) -> two Dreadstalkers, target 32 (DEST_CASTER_SUMMON, Summon Felguard pattern). eff2 DUMMY target 6 requires an enemy target. Cooldown Haste allow list already widened by WP-0 (Player.cpp:160). No NOT_SHAPESHIFTED. SpellClassSet 5, no family bits.',
    raw_overrides={'ProcChance': 101, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 1021, 'EffectMiscValueB_2': 1021, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': "Summons 2 Dreadstalkers to attack your target for 12 sec, each biting for $200830s1 Shadow damage every 2 sec. When they depart, you gain Molten Core. Molten Core: Your next Soul Fire is instant. Stacks up to 4 times. Lasts 30 sec.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 5, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'DefenseType': 1, 'PreventionType': 1, 'InterruptFlags': 15, 'FacingCasterFlags': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)
scripted_by(call_dreadstalkers_200829, 'spell_warl_call_dreadstalkers')


summon_doomguard_200831 = spell(
    id=200831,
    name='Summon Doomguard',
    school=School.SHADOW,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=20,
    range_yards=0.0,
    duration_ms=26000,
    effects=[
        Effect(type=EffectType.SUMMON, implicit_target_a=32, misc_value=300153),
    ],
    spell_icon_id=90163,
    notes='warlock-rework DEMONOLOGY §5.1: learned by Legion\'s Call 200905 (not the trainer). SpellClassSet 5, SpellClassMask_3 = SUMMON_DOOMGUARD (Nemesis). No NOT_SHAPESHIFTED. props 1021, target 32 (DEST_CASTER_SUMMON).',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 1021, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Doomguard to fight for you for 26 sec, casting Doom Bolt at your target.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 5, 'SpellClassMask_3': m.SUMMON_DOOMGUARD, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'DefenseType': 1, 'PreventionType': 1, 'InterruptFlags': 15, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)
skill_line_ability(id=30478, skill_line=354, spell_id=200831, class_mask=256)


summon_infernal_200833 = spell(
    id=200833,
    name='Summon Infernal',
    school=School.FIRE,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=20,
    range_yards=30.0,
    duration_ms=26000,
    effects=[
        Effect(type=EffectType.SUMMON, implicit_target_a=87, misc_value=300154),
    ],
    spell_icon_id=460,
    notes='warlock-rework DEMONOLOGY §5.1/§0.2.5: learned by Legion\'s Call 200905. Ground-target (Targets 0x40, implicit_target_a=87 DEST_DEST). No impact damage/stun (spec §5). SpellVisualID_1 4859 = stock Inferno (1122) visual, the green meteor on its InstantAreaKit. SpellClassSet 5, SpellClassMask_3 = SUMMON_INFERNAL (Nemesis, Destro Cataclysm mask-only join). Separate cooldown category from Doomguard (no shared category).',
    raw_overrides={'Targets': 64, 'CastingTimeIndex': 1, 'ProcChance': 101, 'EquippedItemClass': -1, 'EffectMiscValueB_1': 1021, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons an Infernal to fight for you for 26 sec, burning nearby enemies with Immolation Aura.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': 5, 'SpellClassMask_3': m.SUMMON_INFERNAL, 'SpellVisualID_1': 4859, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'DefenseType': 1, 'PreventionType': 1, 'InterruptFlags': 15, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)
skill_line_ability(id=30479, skill_line=354, spell_id=200833, class_mask=256)
scripted_by(summon_infernal_200833, 'spell_warl_summon_infernal')


demonic_taunt_200839 = spell(
    id=200839,
    name='Demonic Taunt',
    school=School.SHADOW,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=8000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=30.0,
    duration_ms=3000,
    effects=[
        Effect(type=EffectType.THREAT, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_TAUNT),
    ],
    spell_icon_id=150,
    notes='warlock-rework DEMONOLOGY §5.2: Dark Apotheosis only (ShapeshiftMask=0x400000, form 23 bit). eff0 ATTACK_ME (114) target 6, eff1 MOD_TAUNT target 6. Learned by carrier 200864.',
    raw_overrides={'ShapeshiftMask': 4194304, 'CastingTimeIndex': 1, 'ProcChance': 101, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Taunts the target to attack you for $d. Dark Apotheosis only.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Taunted.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 0, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'DefenseType': 1, 'PreventionType': 1, 'InterruptFlags': 15, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)
skill_line_ability(id=30480, skill_line=354, spell_id=200839, class_mask=256)


hand_of_guldan_200820 = spell(
    id=200820,
    name="Hand of Gul'dan",
    school=School.SHADOW | School.FIRE,
    attributes=65536,
    cast_time_ms=1500,
    cooldown_ms=12000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=54, points_per_level=5.177966101694915, die_sides=4, implicit_target_a=6),
        Effect(type=EffectType.DUMMY, base_points=2, implicit_target_a=6),
    ],
    spell_icon_id=90160,
    notes="warlock-rework DEMONOLOGY §4.1: baseline castable, learn 10 (B20). Shadowflame (School.SHADOW|FIRE=36). eff0 SCHOOL_DAMAGE via _scaling.sb_units(0.65, 10, 313, 316) (@60 313-316, @80 417-420). eff1 DUMMY stored 2 (= 3 Wild Imps, $s2, live=stored+1 via default die_sides=1). NOT_SHAPESHIFTED (Metamorphosis/Dark Apotheosis admit it via their own aura-275 masks). Icon fallback 2340 (mined 90160 not built this pass, optional per §2.5). SpellVisualID_1 90025 = Ascension's falling fel meteor + crater (patch_warlock_vfx_models.py).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Calls down a demonic meteor on the target, dealing $s1 Shadowflame damage and summoning $s2 Wild Imps. While you are in Metamorphosis, it also deals $200821s1 Shadowflame damage to all other enemies within 8 yards of the target. Wild Imps cast Fel Firebolt at your target and last up to 60 sec.", 'EffectBonusMultiplier_1': 0.5571, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_3': m.HAND_OF_GULDAN, 'SpellClassSet': 5, 'SpellVisualID_1': 90025, 'BaseLevel': 10, 'SpellLevel': 10, 'Speed': 0.0, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
trained_by(hand_of_guldan_200820, 214, 10, 600)
trained_by(hand_of_guldan_200820, 215, 10, 600)
skill_line_ability(id=30472, skill_line=354, spell_id=200820, class_mask=256)
scripted_by(hand_of_guldan_200820, 'spell_warl_hand_of_guldan')


bane_of_doom_200825 = spell(
    id=200825,
    name='Bane of Doom',
    school=School.SHADOW,
    dispel=DispelType.CURSE,
    attributes=65536,
    category=0,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=15,
    range_yards=30.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=131, points_per_level=6.372881355932203, die_sides=4, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=6000),
    ],
    spell_icon_id=91,
    notes="warlock-rework DEMONOLOGY §4.2 (B14/B15): baseline castable, learn 20. Bane, not a curse-slot curse - dispel=CURSE, category 0 (not stock Curse of Doom's 1179, C27), joins spell_group 1202 (bane slot) below, Warlock::IsBane extended by WP-0. eff0 via _scaling.sb_units(0.80, 20, 386, 389) (@60 386-389, @80 514-517), amplitude 6000 (haste adds ticks automatically). AttributesEx6 copied from Curse of Agony/Doom's.",
    raw_overrides={'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Suffering Shadow damage over time.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Inflicts impending doom on the target, causing $o1 Shadow damage over $d. Bane of Doom does not occupy your curse slot and can be active on several targets at once. Only one Bane per target.', 'EffectBonusMultiplier_1': 0.6856, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'MaxLevel': 80, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_3': m.BANE_OF_DOOM, 'SpellClassSet': 5, 'SpellLevel': 20, 'SpellVisualID_1': 5019, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
trained_by(bane_of_doom_200825, 214, 20, 2000)
skill_line_ability(id=30473, skill_line=354, spell_id=200825, class_mask=256)
spell_group(1202, bane_of_doom_200825)


unending_resolve_200826 = spell(
    id=200826,
    name='Unending Resolve',
    school=School.SHADOW,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=RANGE_SELF,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-41, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=9),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=26),
    ],
    spell_icon_id=1981,
    notes='warlock-rework DEMONOLOGY §4.3: baseline castable, learn 25. Off the GCD (StartRecoveryCategory/Time 0/0). No NOT_SHAPESHIFTED (usable in both forms). cooldown_ms 180000 (>=30s, Cooldown Haste eligible). eff0 -41 stored (-40% damage taken live). eff1/eff2 silence/interrupt immunity (mechanic 9/26).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage taken reduced by 40%. Immune to silence and interrupt effects.', 'BaseLevel': 25, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Hardens your soul, reducing all damage taken by 40% and making you immune to interrupt and silence effects for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_3': m.UNENDING_RESOLVE, 'SpellClassSet': 5, 'SpellLevel': 25, 'StartRecoveryCategory': 0, 'StartRecoveryTime': 0},
)
trained_by(unending_resolve_200826, 214, 25, 3000)
skill_line_ability(id=30474, skill_line=354, spell_id=200826, class_mask=256)
scripted_by(unending_resolve_200826, 'spell_warl_unending_resolve')


# shapeshift_form(23) server-side override row (WP-T table) - matches Metamorphosis's live flags
# 0xd8 (0x80 CAN_USE_ITEMS | 0x40 CAN_USE_EQUIPPED_ITEMS | 0x8 CAN_NPC_INTERACT | 0x10), per the
# "known gap" note (DEMONOLOGY-WP-BRIEF): client-side SpellShapeshiftForm.dbc row 23 is NOT shipped
# in the patch this pass (shapeshift_form() is server-only, registry.py - no client patch is
# produced for this table); this is a playtest-time verification item (§11 Q26). modelID_A 25277 =
# Metamorphosis form 22's own display (DemonForm.mdx, the only stock display on that model) - the
# server sets the display from this row (Unit::GetModelForForm; horde falls back to modelID_A), so
# no client row is needed for the model either.
shapeshift_form(23, flags1=0xd8, modelID_A=25277)
