"""
Mage - spells that are never directly cast - proc/periodic-tick effects, trigger_spell targets, hidden talent-rank buffs, etc..

Split from a single source/classes/mage.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .mage_...` below) resolve.
"""

from lib.dsl import AuraType, CombatRating, DispelType, Effect, EffectType, Mechanic, PowerType, School, SpellModOp
from lib.dsl.registry import bonus_coefficients, procs_on, scripted_by, spell


arcane_missile_7268 = spell(
    id=7268,
    name='Arcane Missile',
    school=School.ARCANE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=23, points_per_level=3.3, implicit_target_a=77),
    ],
    spell_icon_id=225,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 8); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80 | Bugfix (playtest report, 2026-09-08): SpellVisualID_1 was left at rank 1\'s own value (268) instead of being carried over from the max rank\'s damage sub-spell (25346, mage.csv/npc.csv - SpellVisualID_1 270) like every other field in this bootstrap was - "arcane missiles has the rank 1 model instead of the max rank model for its missiles". Fixed to 270.',
    raw_overrides={'AttributesEx2': 4, 'AttributesEx3': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 8, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Launches Arcane Missiles at the enemy, causing $7268s1 Arcane damage every $5143t2 sec for $5143d.', 'EffectBonusMultiplier_1': 0.28600001335144043, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 8, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 20.0, 'SpellClassMask_1': 2097152, 'SpellClassSet': 3, 'SpellLevel': 8, 'SpellPriority': 50, 'SpellVisualID_1': 270},
)


chilled_12484 = spell(
    id=12484,
    name='Chilled',
    school=School.FROST,
    mechanic=Mechanic.SNARE,
    attributes=256,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=1500,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-26, implicit_target_a=6, apply_aura=AuraType.MOD_DECREASE_SPEED),
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_HEALING_PCT, misc_value=127),
    ],
    spell_icon_id=285,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 136, 'AttributesEx2': 4, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement Slowed.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Chills the target for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 1048576, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellVisualID_1': 2640},
)


silenced_improved_counterspell_18469 = spell(
    id=18469,
    name='Silenced - Improved Counterspell',
    school=School.ARCANE,
    dispel=DispelType.MAGIC,
    mechanic=Mechanic.SILENCE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=2000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=6, apply_aura=AuraType.MOD_SILENCE),
    ],
    spell_icon_id=17,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 136, 'AttributesEx2': 4, 'AttributesEx3': 1073872896, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Silenced.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Silences the target for $d.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 1073741824, 'SpellClassSet': 3},
)


molten_armor_34913 = spell(
    id=34913,
    name='Molten Armor',
    school=School.FIRE,
    attributes=150994944,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=74, points_per_level=5.2778, implicit_target_a=6),
    ],
    spell_icon_id=2307,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 62); RealPointsPerLevel from rank1→top rank's own top level (80, chain has a gap at 60) slope (anchor rank 43044, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (43044, rank 3); MaxLevel set to 80",
    raw_overrides={'AttributesEx': 168, 'AttributesEx2': 16388, 'AttributesEx4': 16512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 62, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes $34913s1 Fire damage when hit, increases your chance to critically hit with spells by $30482s3% of your Spirit, and reduces the chance you are critically hit by $30482s2%.  Only one type of Armor spell can be active on the Mage at any time.  Lasts $30482d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassMask_2': 8, 'SpellClassSet': 3, 'SpellLevel': 62},
)


blizzard_42208 = spell(
    id=42208,
    name='Blizzard',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=35, points_per_level=4.4, implicit_target_a=76, implicit_target_b=16, radius_yards=8.0),
    ],
    spell_icon_id=285,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 136, 'AttributesEx2': 1073741824, 'AttributesEx3': 1073741824, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Ice shards pelt the target area doing ${$42208m1*8*$<mult>} Frost damage over $10d.', 'EffectBonusMultiplier_1': 0.14300000667572021, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 135, 'SpellClassMask_1': 524416, 'SpellClassSet': 3, 'SpellDescriptionVariableID': 167, 'SpellLevel': 20, 'SpellPriority': 50, 'SpellVisualID_1': 9487, 'StartRecoveryCategory': 133},
)


fiery_payback_44440 = spell(
    id=44440,
    name='Fiery Payback',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=-1751, implicit_target_a=1, apply_aura=107, misc_value=10),
        Effect(type=EffectType.APPLY_AURA, base_points=2499, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=3189,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1→level-60 slope; coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CasterAuraState': 13, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "When below 35% health all damage taken is reduced by $s1% and your Pyroblast spell's cast time is reduced by ${$44440m2/-1000}.2 secs while the cooldown is increased by ${$44440m3/-1000}.1 secs.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 8, 'EffectSpellClassMaskB_1': 4194304, 'EffectSpellClassMaskC_1': 4194304, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


living_bomb_44461 = spell(
    id=44461,
    name='Living Bomb',
    school=School.FIRE,
    attributes=159711232,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=305, points_per_level=14.7692, implicit_target_a=53, implicit_target_b=16, radius_yards=10.0),
    ],
    spell_icon_id=3000,
    notes="single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 60); RealPointsPerLevel from rank1→top rank's own top level (86, chain has a gap at 60) slope (anchor rank 55362, rank 3); coefficient/cast_time_ms/mana_cost_pct from max rank (55362, rank 3); MaxLevel set to 80",
    raw_overrides={'AttributesEx2': 1073741824, 'AttributesEx5': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The target becomes a Living Bomb, taking $44457o1 Fire damage over $44457d.  After $44457d or when the spell is dispelled, the target explodes dealing $44461s1 Fire damage to all enemies within $44461a1 yards.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 0.4000000059604645, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 12582935, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassMask_2': 65536, 'SpellClassSet': 3, 'SpellLevel': 60, 'SpellPriority': 50, 'SpellVisualID_1': 10693},
)


icicles_200001 = spell(
    id=200001,
    name='Icicles',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=35,
    notes='Frost Mage rework (docs/frost-mage-redesign.md sec 1, Icicles): stacking (CumulativeAura=5) caster buff, no fixed duration (cleared explicitly by spell_mage_icicles on combat-leave or by Glacial Spike on cast). Generation gated in C++ on the caster knowing SPELL_MAGE_GLACIAL_SPIKE (200002), granted by Frostbolt/Frostfire Bolt casts and every 4th Blizzard tick - see spell_mage.cpp. SpellIconID 35 (Spell_Frost_Glacier, from apps/dbc-tools/var/spell_icon_names.csv).',
    raw_overrides={'AttributesEx3': 1073741824, 'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Frost energy has gathered around you. Stacks up to 5 times; consumed by Glacial Spike.', 'CumulativeAura': 5, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Frost energy has gathered around you. Stacks up to 5 times; consumed by Glacial Spike.', 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 3, 'SpellPriority': 50, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 0},
)


shattering_cold_200003 = spell(
    id=200003,
    name='Shattering Cold',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    range_yards=40.0,
    duration_ms=4000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=6, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2945,
    notes='Frost Mage rework (docs/frost-mage-redesign.md sec 1, Shattering Cold): target-side debuff applied by Flurry (spell_mage_flurry, spell_mage.cpp) on bolt impact. Not dispellable (dispel=DispelType.NONE). Caster-scoping ("only the applying caster benefits") and the frozen-state check are done in C++ via target->HasAura(SPELL_MAGE_SHATTERING_COLD, casterGuid) - see FrostMageRework::IsFrozenFor in spell_mage.cpp - deliberately not via CasterAuraState/AURA_STATE_FROZEN, which is a global (not per-caster) flag in this engine; see docs/frost-mage-implementation-plan.md\'s correction. SpellIconID 2945 (Ability_Mage_ShatterShield, from apps/dbc-tools/var/spell_icon_names.csv). SpellVisualID still unset pending an art pass. Playtest bugfix (2026-08-27, user report): range_yards was left null, which reuse.py\'s range_index() maps to RangeIndex 0 - not "unlimited", but the real client\'s near-zero/self-only SpellRange.dbc row 0 (Spell.cpp\'s CheckCast only special-cases RangeEntry->ID == 1 for triggered 0-range spells, not 0). Every Flurry cast\'s caster->CastSpell(target, 200003, true) silently failed SPELL_FAILED_OUT_OF_RANGE against a non-self target, so the debuff never applied - confirmed live via temporary LOG_ERROR tracing. Set to 40yd to match Flurry\'s own range (200004), since Shattering Cold can only ever be triggered on whatever Flurry already hit.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': "This target's frozen state is being exploited by the caster's spells and abilities.", 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "This target's frozen state is being exploited by the caster's spells and abilities.", 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 3, 'SpellPriority': 50, 'StartRecoveryCategory': 133},
)


glacial_spike_windup_1_200025 = spell(
    id=200025,
    name='Glacial Spike (Windup 1)',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    range_yards=10.0,
    effects=[
        Effect(type=EffectType.DUMMY, implicit_target_a=87),
    ],
    spell_icon_id=1236,
    notes="Frost Mage rework - internal plumbing spell, not player-facing, and no longer cast by anything (2026-09-18: the post-cast cosmetic ramp this was the first leg of was replaced by a WorldEffect on 200002's own CastKit, so the icicles visual plays during the cast bar instead of after it - see 200002's notes and spell_mage_glacial_spike's class comment in spell_mage.cpp). Row kept, unused, same 'orphaned but harmless' precedent as frozen_orb_periodic_200009. SpellVisualID_1 90006 (patch_mage_vfx_models.py, also now orphaned).",
    raw_overrides={'SpellClassSet': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'EquippedItemClass': -1, 'PreventionType': 1, 'ProcChance': 101, 'SpellPriority': 50, 'Description_Lang_enUS': 'Internal: first cosmetic wind-up hop for Glacial Spike.', 'Speed': 1.0, 'SpellVisualID_1': 90006},
)


glacial_spike_windup_2_200026 = spell(
    id=200026,
    name='Glacial Spike (Windup 2)',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    range_yards=10.0,
    effects=[
        Effect(type=EffectType.DUMMY, implicit_target_a=87),
    ],
    spell_icon_id=1236,
    notes="Frost Mage rework - internal plumbing spell, not player-facing, and no longer cast by anything - see 200025's notes (same reason, same date). Row kept, unused. SpellVisualID_1 90007 (patch_mage_vfx_models.py, also now orphaned) - its MissileModel (cfx_mage_glacialspike_convergingmissiles) is reused directly as a WorldEffect on 200002's CastKit instead (KIT_GLACIALSPIKE_CAST, patch_mage_vfx_models.py).",
    raw_overrides={'SpellClassSet': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'EquippedItemClass': -1, 'PreventionType': 1, 'ProcChance': 101, 'SpellPriority': 50, 'Description_Lang_enUS': 'Internal: second cosmetic wind-up hop for Glacial Spike.', 'Speed': 5.0, 'SpellVisualID_1': 90007},
)


glacial_spike_impact_200027 = spell(
    id=200027,
    name='Glacial Spike (Impact)',
    school=School.FROST,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=1499, implicit_target_a=6),
    ],
    spell_icon_id=1236,
    coeff_weight=1.2,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 1, Glacial Spike): the real, damage-dealing leg - same flat 1500 base Frost damage (EffectBasePoints stored as 1499) with a 1.2 spell power coefficient this row carried under ID 200002 before the original ramp redesign (see that row's notes and docs/frost-mage-handoff.md's art-pass discussion). The spell_bonus_data row (direct_bonus=1.2) moved here from 200002 - see the accompanying pending_db_world SQL. Fired via caster->CastSpell(target, 200027, true) from spell_mage_glacial_spike::LaunchImpact (spell_mage.cpp) immediately when the player's 2.5s cast completes - no post-cast delay (2026-09-18: previously ~800ms after cast completion, via an intermediate 200025->200026 cosmetic ramp; removed once the icicles-converging visual moved onto 200002's own CastKit, see 200002's notes). Icicle consumption, Fingers-of-Frost-charge consumption, and the Arctic Winds R3 shatter-cleave (spell_mage_glacial_spike_impact::ConsumeIciclesAndFrostCharge) all live here, since this is the stage that represents the spell actually landing - not yet implemented is Arctic Winds R3's cleave depending on the Row 9 Arctic Winds talent, same TODO as before. SpellIconID 1236 (Spell_Frost_IceShard, from apps/dbc-tools/var/spell_icon_names.csv). Speed 60 (doubled from 30 on 2026-09-18 playtest feedback - the missile visibly travels too slowly at 30). SpellVisualID_1 90008 (patch_mage_vfx_models.py): HasMissile/MissileModel=cfx_mage_iciclemastery_launchedmissile (the actual spike in flight - not from the cfx_mage_glacialspike_* asset family; both cfx_mage_glacialspike_launchedmissile and cfx_mage_glacialspike_dummyholdmissile were tried first and rejected on 2026-09-18 playtest feedback for looking like mostly particle effects with little solid mesh live. iciclemastery_launchedmissile was found by browsing patch-N.MPQ for any Spike/Glacial/Icicle-named model and user-confirmed correct after inspecting it in a model viewer) + ImpactKit wrapping cfx_mage_glacialspike_impactchest for the hit. See docs/reworks/fire-mage-meteor-vfx.md.",
    raw_overrides={'SpellClassSet': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'EquippedItemClass': -1, 'PreventionType': 1, 'ProcChance': 101, 'SpellPriority': 50, 'Description_Lang_enUS': 'Consumes all Icicles to hurl a massive spike of ice at the target, dealing Frost damage.', 'DefenseType': 1, 'Speed': 60.0, 'SpellVisualID_1': 90008},
)


flurry_bolt_200037 = spell(
    id=200037,
    name='Flurry (Bolt)',
    school=School.FROST,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=99, implicit_target_a=6),
    ],
    spell_icon_id=187,
    coeff_weight=0.3,
    notes="Frost Mage rework - internal plumbing spell, not player-facing (never cast by a player directly). One of 3 sequential bolts fired by spell_mage_flurry::FireBolts (spell_mage.cpp) - cast via caster->CastSpell(target, 200037, true) at 0ms/200ms/400ms after Flurry's (200004) own cast completes, target re-resolved by GUID + ObjectAccessor for the 2nd/3rd bolt same as Glacial Spike's old ramp did (see FireBolts' own comment). Same per-bolt numbers as the pre-redesign 200004 (100 base each, EffectBasePoints stored as 99, 0.3 spell power coefficient via this row's own spell_bonus_data), just split into 3 separately-cast, separately-scaled, separately-timed instances instead of 3 simultaneous effects on one entry - total damage output unchanged, only the pacing/visual changed (2026-09-18 playtest feedback: wanted a genuine burst of 3 sequential bolts, not one bolt worth of triple damage). Shattering Cold (200003) is applied once, right after the 3rd/last bolt is cast (not from this row) - FireBolts casts it in the same scheduled callback as the final bolt, preserving 'Flurry's own bolts do not benefit from Shattering Cold' on a best-effort/cast-order basis; note this has no live consumer yet (FrostMageRework::IsFrozenFor/HasShatteringCold, spell_mage.cpp, are currently uncalled - see docs/frost-mage-implementation-plan.md), so nothing currently depends on this ordering being exact down to travel-time precision. SpellIconID 187 (Spell_Frost_ChillingBlast, apps/dbc-tools/var/spell_icon_names.csv). SpellVisualID_1 90010 (patch_mage_vfx_models.py): HasMissile/MissileModel=cfx_mage_flurry_missile + ImpactKit wrapping cfx_mage_flurry_impactchest - the missile/impact visual 200004's own SpellVisualID_1 (90009) used to carry, moved here since this is what actually travels and hits now. See docs/reworks/fire-mage-meteor-vfx.md.",
    raw_overrides={'SpellClassSet': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'EquippedItemClass': -1, 'PreventionType': 1, 'ProcChance': 101, 'SpellPriority': 50, 'Description_Lang_enUS': 'Internal: one bolt of Flurry.', 'Speed': 38.0, 'DefenseType': 1, 'SpellVisualID_1': 90010},
)


restore_mana_200005 = spell(
    id=200005,
    name='Restore Mana',
    school=School.NORMAL,
    attributes=402653440,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    effects=[
        Effect(type=137, base_points=29, implicit_target_a=1),
    ],
    spell_icon_id=1036,
    notes='Frost Mage rework (docs/frost-mage-redesign.md sec 2, Conjure Mana Gem): "the new item should restore 30% of maximum mana." SPELL_EFFECT_ENERGIZE_PCT (type 137) is a real, native effect (Spell::EffectEnergizePct, SpellEffects.cpp:1995 - CalculatePct(maxPower, damage)) - no C++ needed, unlike what an earlier pass of the implementation plan assumed. base_points=29 -> 30% (-1 convention, die_sides=1). Wired to item 5514 (Mana Agate)\'s spellid_2 slot in the accompanying pending SQL, replacing the old flat spell 5405; 5405 itself is left untouched since it\'s shared with unrelated items 36799/9397.',
    raw_overrides={'SpellClassSet': 3, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Restores 30% of maximum mana.', 'EquippedItemClass': -1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellPriority': 50, 'SpellClassMask_3': 16},
)


refreshment_200006 = spell(
    id=200006,
    name='Refreshment',
    school=School.NORMAL,
    attributes=402653440,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=84),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=85),
    ],
    spell_icon_id=358,
    notes='Frost Mage rework (docs/frost-mage-redesign.md sec 2, Conjure Refreshment): item 43518 ("Conjured Mana Pie") repointed to this spell in the accompanying pending SQL (spellid_1, was the real pulled-data spell 61828 "Refreshment", a flat-value wrapper around 61829 "Food"/61830 "Drink"). Built on the same native Food/Drink mechanism those real IDs use - SPELL_AURA_MOD_REGEN (84) and SPELL_AURA_MOD_POWER_REGEN (85), MiscValue POWER_MANA (0) on effect 2 - rather than a dedicated periodic aura, so the real client "eating/drinking" emote (Player.cpp keys it off these two aura types specifically) comes for free. Per-tick amount is still computed in C++ (spell_mage_refreshment, spell_mage.cpp) via OnEffectCalcAmount reading GetMaxHealth()/GetMaxPower(POWER_MANA) - no DBC field can express "percent of current max" - targeting 105%, not 100%, of max over the 30s duration to comfortably outrun MOD_REGEN\'s health tick-count imprecision (it only ticks on the player\'s global un-reset-on-apply 2-sec regen timer); RegenerateHealth()/Regenerate(POWER_MANA) both clamp at max already, so overshooting the math costs nothing beyond wasted regen once full. AuraInterruptFlags reuses the real spells\' NOT_SEATED|NOT_ABOVEWATER combo (262272) - the engine auto-sits the player on apply and drops the aura on standing (Unit.cpp), so no extra stand-state handling is needed. SpellIconID 358 (the native Food/Drink icon, same one 61828/61829/61830 use).',
    raw_overrides={'SpellClassSet': 0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Restores health and mana over $d.  Must remain seated while eating.', 'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Restoring health and mana.', 'EquippedItemClass': -1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellPriority': 50, 'AuraInterruptFlags': 262272, 'InterruptFlags': 1, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


frozen_orb_pulse_200008 = spell(
    id=200008,
    name='Frozen Orb Pulse',
    school=School.FROST,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    radius_yards=10.0,
    duration_ms=4000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=199, implicit_target_a=16),
        Effect(type=EffectType.APPLY_AURA, base_points=-31, mechanic=Mechanic.SNARE, implicit_target_a=16, apply_aura=AuraType.MOD_DECREASE_SPEED),
    ],
    spell_icon_id=2132,
    coeff_weight=0.15,
    notes='Frost Mage rework (docs/frost-mage-redesign.md sec 1, Frozen Orb\'s pulse): "Every 1 sec, deals 200 Frost damage plus 0.15 spell power coefficient to all enemies within 10 yards, and applies a chill reducing movement speed by 30% for 4 sec." Two effects on one row, same shape as the real Cone of Cold (120): SCHOOL_DAMAGE (base_points 199, -1 convention) + APPLY_AURA MOD_DECREASE_SPEED (base_points -31, -1 convention for -30%, EffectMechanic MECHANIC_SNARE=11), both TARGET_UNIT_DEST_AREA_ENEMY (16, not the SRC variant this row originally shipped with - see "Cast by" below for why). Neither effect JSON sets its own "radius_yards" key (build.py only falls back to the row\'s top-level radius_yards when the per-effect key is absent, not when it\'s present-but-null - learned the hard way diffing a hand-built row against generate.py\'s actual output), so both inherit the row\'s radius_yards (10, -> EffectRadiusIndex 13, the same row Cone of Cold\'s own radius already reuses) and duration_ms (4000, -> DurationIndex 35, the same row Shattering Cold/200003 already reuses). Coefficient (0.15) goes through spell_bonus_data like every other new spell this session - see the accompanying pending SQL. Cast by the OWNING PLAYER (not the orb) at an explicit dest = the orb\'s live position, once per second, from npc_mage_frozen_orb::UpdateAI (spell_mage.cpp) - a deliberate change from the original SRC-based "orb self-casts via a periodic aura (200009)" design, which silently attributed all damage/threat/combat-log entries to the orb instead of the player (root-caused via live playtest: FoF procced and the pulse showed in the combat log, but never in the player\'s own damage meter). TARGET_UNIT_DEST_AREA_ENEMY lets the player be the actual spell caster (correct attribution *and* correct spell-power scaling off the player\'s own stats) while still centering the AoE on the orb\'s moving position rather than the stationary player. 200009 (Frozen Orb Periodic) is no longer cast by anything - left as an orphaned row rather than deleted, see spell_mage.cpp\'s own notes. spell_mage_frozen_orb_pulse (spell_mage.cpp) still exists for BoostChillEffect (Chilled to the Bone) and to tell the orb\'s AI a pulse landed (halts movement, starts the FoF grant chain) - it does not touch the damage/slow itself, both of which are native DBC effects needing no script. Attributes=0 and no player-facing name/description text (Description_Lang_Mask=0) - never cast directly by a player action, never shown in a spellbook/tooltip.',
    raw_overrides={'SpellClassSet': 0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 0, 'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Movement speed reduced.', 'EquippedItemClass': -1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellPriority': 50},
)


frozen_orb_periodic_200009 = spell(
    id=200009,
    name='Frozen Orb Periodic',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=1000, trigger_spell=frozen_orb_pulse_200008.id),
    ],
    spell_icon_id=2132,
    notes='Frost Mage rework (docs/frost-mage-redesign.md sec 1, Frozen Orb): the orb\'s own self-buff, cast on itself once by npc_mage_frozen_orb::IsSummonedBy (spell_mage.cpp) right after summon. SPELL_AURA_PERIODIC_TRIGGER_SPELL (apply_aura 23) at 1000ms amplitude, triggering 200008 (Frozen Orb Pulse) - docs/frost-mage-implementation-plan.md\'s Frozen Orb section: "Put a self-cast aura on the orb using SPELL_AURA_PERIODIC_TRIGGER_SPELL at a 1000ms amplitude." duration_ms=10000 (DurationIndex 1) matches both the spec\'s "10 sec" travel time and the orb\'s own TEMPSUMMON_TIMED_DESPAWN lifetime, so exactly 10 pulses land before everything cleans up together. Attributes=0, no player-facing text - never cast by a player.',
    raw_overrides={'SpellClassSet': 0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 0, 'EquippedItemClass': -1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellPriority': 50},
)


arcane_blast_debuff = spell(
    id=36032,
    name='Arcane Blast',
    school=School.ARCANE,
    attributes=67371008,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=79, misc_value=64),
        Effect(type=EffectType.APPLY_AURA, base_points=174, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=2294,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Phase 3) - moved from npc.csv, where pull.py\'s file-guess heuristic first landed it (same misfile pattern as earlier batches). Real stock \'Arcane Blast\' stacking self-buff (effect1: +15%/stack Arcane dmg, raw_overrides.CumulativeAura=4 max stack; effect2: raises Arcane Blast\'s own mana cost per stack, self-scoped classmask) - cast as Arcane Blast (30451)\'s trigger spell by the existing spell_mage_arcane_blast::HandleAfterCast (spell_mage.cpp). Content untouched, reference only - several Phase 3 items (Arcane Resonance, Arcane Barrage, Arcane Overload, Temporal Convergence) read its live stack count via caster->GetAura(36032)->GetStackAmount(). Bugfix (playtest report, 2026-09-08/09): dropped ProcChance/ProcCharges/ProcTypeMask (100/1/65536) added here in Phase 3 Batch A - they were never needed (stacking is driven entirely by HandleAfterCast\'s CastSpell, not native procs) and turned out to be live: `spell_proc`\'s own explicit row for 36032 has ProcFlags=0, which SpellMgr::LoadSpellProcs() treats as a sentinel and falls back to these DBC fields, making the buff a real (if narrowly classmask-scoped) proc-consumable aura. Confirmed via live debug instrumentation this was firing on every Arcane Barrage cast (redundant with spell_mage_arcane_barrage\'s own intentional removal) and, through a still-unconfirmed adjacent code path, on Arcane Missiles casts too - \\Arcane Missiles still consumes the Arcane Blast debuff\\". Reverting to inert (all three 0/unset',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx2': 268435456, 'AttributesEx3': 196608, 'AttributesEx4': 8388737, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Arcane spell damage increased by $s1% and mana cost of Arcane Blast increased by $s2%.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'CumulativeAura': 4, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Blasts the target with energy, dealing Arcane damage.  Each time you cast Arcane Blast, the damage of all Arcane spells is increased by $36032s1% and mana cost of Arcane Blast is increased by $36032s2%.  Effect stacks up to $36032u times and lasts $36032d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 536870912, 'EffectSpellClassMaskB_1': 536870912, 'EffectSpellClassMaskC_1': 536870912, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassMask_3': 12, 'SpellClassSet': 3, 'SpellLevel': 1},
)


improved_fireball_11069 = spell(
    id=11069,
    name='Improved Fireball',
    school=School.FIRE,
    attributes=262608,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, die_sides=0, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CRITICAL_CHANCE),
    ],
    spell_icon_id=185,
    notes='Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (0,2) rank 1: crit chance instead of the stock cast-time reduction; 3 ranks (ranks 4-5, 12340/12341, are no longer granted).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Fireball by 3%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


improved_frostbolt_11070 = spell(
    id=11070,
    name='Improved Frostbolt',
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
    ],
    spell_icon_id=188,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Frostbolt and Ice Lance spells by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 131104, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


frostbite_11071 = spell(
    id=11071,
    name='Frostbite',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=12494),
    ],
    spell_icon_id=119,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Dealing direct Frost damage has a $s1% chance to freeze the target for $12494d.  The freeze breaks on damage.\n\n|cFF9D9D9DCapstone Bonus: Increases the damage of your Frost spells against frozen targets based on your Mastery.|r', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_2': 4096, 'EffectSpellClassMaskB_2': 4096, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 5, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassMask_2': 512, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


improved_fire_blast_11078 = spell(
    id=11078,
    name='Improved Fire Blast',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=12,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Fire Blast spell by $/1000;S1 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


improved_fire_blast_11080 = spell(
    id=11080,
    name='Improved Fire Blast',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-2001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=12,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Fire Blast spell by $/1000;S1 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


burning_soul_11083 = spell(
    id=11083,
    name='Burning Soul',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.NOT_LOSE_CASTING_TIME),
        Effect(type=EffectType.APPLY_AURA, base_points=1, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MOD_SPELL_CRIT_CHANCE),
    ],
    spell_icon_id=11,
    notes='Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (0,3) rank 1: pushback reduction to 100% at every rank (still scoped to Fire spells via the stock classmask on Effect_1), threat reduction replaced by flat spell crit. Rank 3 is new (200102).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell critical strike chance by 1%. Reduces spell pushback suffered from damaging attacks by 100%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194325, 'EffectSpellClassMaskA_2': 4096, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


molten_shields_11094 = spell(
    id=11094,
    name='Molten Shields',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=107, misc_value=12),
    ],
    spell_icon_id=16,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes your Fire Ward and Frost Ward spells to have a $s1% chance to reflect the warded spell while active. In addition, your Molten Armor has a 50% chance to affect ranged and spell attacks.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 264, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


improved_scorch_11095 = spell(
    id=11095,
    name='Improved Scorch',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=22959),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=816,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your chance to critically hit with Scorch, Fireball and Frostfire Bolt by an additional $s2% and your damaging Scorch spells have a $h% chance to cause your target to be vulnerable to spell damage, increasing spell critical strike chance against that target by $22959s1% and lasts $22959d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 16, 'EffectSpellClassMaskB_1': 17, 'EffectSpellClassMaskB_2': 4096, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 33, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellPriority': 50},
)


flame_throwing_11100 = spell(
    id=11100,
    name='Flame Throwing',
    school=School.FIRE,
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
    spell_icon_id=136,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (2,0) rank 1: 6 yards at both ranks per the spec's tooltip (stock was 3/6). Rank 2's capstone (one 20%-faster Fireball per 12 sec, user call 2026-09-15) is a Phase 3 script keyed on HasAura(12353).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of all Fire spells except Frostfire Bolt by 6 yards.\n\n|cFF9D9D9DCapstone Bonus: The cast time of your Fireball is reduced by 20%. This effect becomes inactive for 12 sec after use.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194327, 'EffectSpellClassMaskA_2': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


impact_11103 = spell(
    id=11103,
    name='Impact',
    school=School.FIRE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=64343),
    ],
    spell_icon_id=45,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 136, 'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your damaging spells a $h% chance to cause the next Fire Blast you cast to stun the target for $12355d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 4, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


world_in_flames_11108 = spell(
    id=11108,
    name='World in Flames',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=2948,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the critical strike chance of your Flamestrike, Pyroblast, Blast Wave, Dragon's Breath, Living Bomb, Blizzard and Arcane Explosion spells by $s1%.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 12587140, 'EffectSpellClassMaskA_2': 65600, 'EffectSpellClassMaskB_1': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


critical_mass_11115 = spell(
    id=11115,
    name='Critical Mass',
    school=School.FIRE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=71, misc_value=4),
    ],
    spell_icon_id=117,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Fire spells by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 12582935, 'EffectSpellClassMaskA_2': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


ignite_11119 = spell(
    id=11119,
    name='Ignite',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=17, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=937,
    notes='Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (1,0) rank 1: 3 ranks (was 5), percentage rescaled to 17; EFFECT_0 DUMMY carries it for spell_mage_ignite / Mage::AddIgniteDamage. Ranks 4-5 (12847/12848) are no longer granted.',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your critical strikes from Fire damage spells cause the target to burn for an additional 17% of your spell's damage over $12654d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 327680, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


ignite_11120 = spell(
    id=11120,
    name='Ignite',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=33, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=937,
    notes='Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (1,0) rank 2: 3 ranks (was 5), percentage rescaled to 33; EFFECT_0 DUMMY carries it for spell_mage_ignite / Mage::AddIgniteDamage. Ranks 4-5 (12847/12848) are no longer granted.',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your critical strikes from Fire damage spells cause the target to burn for an additional 33% of your spell's damage over $12654d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 327680, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


fire_power_11124 = spell(
    id=11124,
    name='Fire Power',
    school=School.FIRE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=31,
    notes='Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (5,2) rank 1: 3 ranks (was 5), 3%. Ranks 4-5 (12399/12400) are no longer granted.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Fire spells by 3%.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 12845079, 'EffectSpellClassMaskA_2': 69704, 'EffectSpellClassMaskB_1': 4194309, 'EffectSpellClassMaskB_2': 135168, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


piercing_ice_11151 = spell(
    id=11151,
    name='Piercing Ice',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=79, misc_value=16),
    ],
    spell_icon_id=176,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Frost spells by $s1%.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 131808, 'EffectSpellClassMaskB_1': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


frost_channeling_11160 = spell(
    id=11160,
    name='Frost Channeling',
    school=School.FROST,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=72, misc_value=16),
        Effect(type=EffectType.APPLY_AURA, base_points=-6, implicit_target_a=1, apply_aura=AuraType.MOD_THREAT, misc_value=16),
    ],
    spell_icon_id=15,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your Frost spells and abilities by $s1% and reduces the threat caused by $s2%. |cFF9D9D9DAt max rank, killing an enemy that yields experience or honor with Frost damage restores 12% of your mana.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 1, 'EffectSpellClassMaskA_1': 655360, 'EffectSpellClassMaskA_2': 2049, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


shatter_11170 = spell(
    id=11170,
    name='Shatter',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=112, misc_value=849),
    ],
    spell_icon_id=976,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of all your spells against frozen targets by 17%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 552211063, 'EffectSpellClassMaskA_2': 1151048, 'EffectSpellClassMaskA_3': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


permafrost_11175 = spell(
    id=11175,
    name='Permafrost',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=999, implicit_target_a=1, apply_aura=107, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=107, misc_value=3),
    ],
    spell_icon_id=143,
    notes='Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 2, Permafrost). Base effect kept the pulled data\'s own numbers (already matched spec\'s 1/2/3 sec duration + 4/7/10% additional slow via the stored+1 convention) but rescoped from the old talent\'s actual shape -- a target-side debuff (duration/slow/heal-received-reduction applied to whoever the mage\'s Frostbolt/Cone of Cold/Frost Nova hit) -- to a caster-side SpellMod pair (SPELLMOD_DURATION + SPELLMOD_EFFECT1, classmask 544 = Frostbolt|Cone of Cold in word A) boosting the caster\'s own cast of those spells, matching every other \'duration+value modifier\' talent this project has built (Arctic Reach, Chilled to the Bone). The old effect3 (SPELLMOD_EFFECT3, -8/-14/-21, confirmed via the Chilled npc-caster spells 6136/7321\'s own effect3 = SPELL_AURA_MOD_HEALING_PCT to be the dropped tooltip\'s \'reduces healing received\' clause) is not in the new spec and was removed outright, not carried forward. \'Frost Shock\' in the redesign\'s talent text was dropped per user decision (2026-08-24) -- not a real Mage spell (Shaman-only in this game), most likely a stray copy-paste word; scoped to Cone of Cold/Frostbolt/Ice Armor only. Ice Armor\'s own melee-reactive slow (6136 Frost Armor / 7321 Ice Armor\'s \'Chilled\' trigger spells, npc.csv) has no SpellFamilyFlags of its own -- same classmask-unreachable shape as Frozen Orb hit this project before -- so it\'s boosted live in spell_mage_chilled (spell_mage.cpp) instead, same \'read the mage\'s own SpellMod amount and fold it in\' idiom as spell_mage_frozen_orb_pulse\'s Chilled to the Bone fix. Capstone (rank 3 only): see effect3. Playtest bugfix (2026-08-27, user report - "Permafrost reduces the effects of everything by 10%, not just move speed"): the SPELLMOD_EFFECT1 modifier\'s classmask (544, Frostbolt|Cone of Cold) was stored under EffectSpellClassMaskA_2, which the naming convention suggests is "effect index 2\'s word A" but which spell_dbc/DBCStructure.h actually reads as "effect index 0(=A)\'s word 2" - dword-major, not effect-major, unlike every other _1/_2/_3-suffixed field in this schema. That left the real target, effect index 1\'s own classmask, all-zero, and SpellInfo::IsAffected treats an all-zero classmask as matching every spell in the family - so the -4/-7/-10% modifier applied unconditionally to EFFECT_0 of every mage spell (including Evocation\'s mana-restore %) instead of just Frostbolt/Cone of Cold. Fixed by moving the value to EffectSpellClassMaskB_1 (effect index 1(=B)\'s word 1), which is what the engine actually reads for effect 1\'s classmask. See data/sql/updates/pending_db_world/frost_mage_rework.sql (merged Frost Mage rework migration; originally rev_1787820084006262155.sql) for the original diagnosis (that migration was a live DB-only patch of the affected rows; this is the matching source-of-truth fix so future full regenerations don\'t reintroduce it).',
    raw_overrides={'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the duration of your Cone of Cold and Frostbolt slow effects by ${{$m1/1000}}.1 sec, and reduces the target's speed by an additional $s2%. Also affects Ice Armor's chilling effect. |cFF9D9D9DAt max rank: each 1 sec you spend moving grants Permafrost, increasing the damage of your next Ice Lance by 20%. Stacks up to 5 times.|r", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 544, 'EffectSpellClassMaskB_1': 544, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


winter_s_chill_11180 = spell(
    id=11180,
    name="Winter's Chill",
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=12579),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=187,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your chance to critically hit with Frostbolt by an additional $s2% and gives your Frost damage spells a $h% chance to apply the Winter's Chill effect, which increases the chance spells will critically hit the target by $12579s1% for $12579d.  Stacks up to $12579u times.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 33, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


improved_blizzard_11185 = spell(
    id=11185,
    name='Improved Blizzard',
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
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=112, misc_value=836),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=108, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=-13, implicit_target_a=1, apply_aura=108, misc_value=19),
    ],
    spell_icon_id=285,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Adds a chill effect to your Blizzard spell.  This effect lowers the target's movement speed by $12484s1%.  Lasts $12484d.  Also reduces the mana cost of Blizzard by $s2% and its periodic interval by $s3%.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 128, 'EffectSpellClassMaskA_1': 128, 'EffectSpellClassMaskA_2': 524416, 'EffectSpellClassMaskA_3': 524416, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


frost_warding_11189 = spell(
    id=11189,
    name='Frost Warding',
    school=School.NORMAL,
    attributes=208,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=108, misc_value=8),
        Effect(type=EffectType.DUMMY, base_points=14),
    ],
    spell_icon_id=501,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the armor and resistances given by your Frost Armor and Ice Armor spells by $s1%.  In addition, gives your Frost Ward and Fire Ward a $s2% chance to negate the warded damage spell and restore mana equal to the damage caused. |cFF9D9D9DAt max rank, while Frost Armor or Ice Armor is active, physical damage taken is reduced by an additional 20%.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


improved_cone_of_cold_11190 = spell(
    id=11190,
    name='Improved Cone of Cold',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=74396),
    ],
    spell_icon_id=35,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 6, Improved Cone of Cold). effect1 (dmg%) kept the pulled data's mechanic/scope (ADD_PCT_MODIFIER, SPELLMOD_DAMAGE, classmask already Cone-of-Cold-only) but retuned 14/24/34 -> 19/39/59 (stored+1 = 20/40/60%, spec's value; old data was a stale/different tuning). effect2 (new, all 3 ranks): FoF-chance-on-hit, same shape as Improved Blizzard's own FoF grant -- native PROC_TRIGGER_SPELL straight to the Fingers of Frost charge spell (74396), 33/66/100% (literal, not stored+1 -- ProcChance convention). ",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage dealt by your Cone of Cold spell by $s1%, and gives it a $h% chance to grant Fingers of Frost. |cFF9D9D9DAt max rank, after casting Cone of Cold, your Blizzard channels twice as fast.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 512, 'EffectSpellClassMaskA_1': 512, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 33, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'ProcTypeMask': 65536, 'EffectSpellClassMaskA_2': 512},
)


ice_shards_11207 = spell(
    id=11207,
    name='Ice Shards',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=1236,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of your Frost spells by $s1%. |cFF9D9D9DAt max rank, increases damage against frozen targets by 6%.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 131808, 'EffectSpellClassMaskA_2': 1052672, 'EffectSpellClassMaskA_3': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


alacrity_11210 = spell(
    id=11210,
    name='Alacrity',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=306, misc_value=4194304),
    ],
    spell_icon_id=2022,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 0): repoints stock Arcane Subtlety\'s slot (id 74) to (0,0). "Increases your cooldown reduction by 5/10/15%." SPELL_AURA_MOD_CUSTOM_STAT_PCT (306), misc_value 1<<CR_COOLDOWN_HASTE (4194304). raw_overrides fully replaced (not merged) - the earlier version of this edit left stale classmask/attribute fields from the real Arcane Subtlety talent this slot used to hold; caught and fixed. Bugfix (playtest report, 2026-09-08): tooltip retitled "Cooldown Haste" to match the actual stat name (docs/itemization-changes.md) rather than the generic "cooldown reduction" phrasing - the underlying mechanic (GetCooldownHastePercentage()) was already correct.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Cooldown Haste by 5%.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


arcane_subtlety_11213 = spell(
    id=11213,
    name='Arcane Subtlety',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=5),
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=72, misc_value=64),
    ],
    spell_icon_id=74,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 1): repoints stock Arcane Concentration\'s slot (id 75) to (1,1), trimmed to 3 ranks. "Increases the range of your damaging spells with a channeling or cast time by 2/4/6 yards." effect1 SPELL_AURA_ADD_FLAT_MODIFIER (107)/SPELLMOD_RANGE (5), EffectSpellClassMaskA_1 (raw_override, NOT the friendly effect misc_value) covering Frostbolt|Fireball|Arcane Blast|Blizzard|Pyroblast|Arcane Missiles - individually verified live via the DB overlay; not exhaustive (Frostfire Bolt, Cone of Cold, a few others not yet verified), flagged for a follow-up data pass. "Reduces the mana cost of your Arcane Spells by 4/8/12%" - effect2 SPELL_AURA_MOD_POWER_COST_SCHOOL_PCT (72), misc_value 64 (Arcane school, not classmask - no scoping risk). Capstone (rank 3 only, "threat reduced by 30%") - effect3 SPELL_AURA_MOD_THREAT (10), misc_value 64. Corrected from an earlier broken version of this edit: the range effect\'s classmask was accidentally written into the friendly effect1 JSON blob instead of raw_overrides (silently ignored there), and stale trigger_spell/classmask/attribute fields from the real Arcane Concentration data this slot used to hold survived a merge instead of being cleared - both caught by generate.py\'s lint WARNING and fixed here with a full (non-merging) rewrite.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of your damaging spells with a channeling or cast time by 2 yards. Reduces the mana cost of your Arcane Spells by 4%.\n\n|cFF9D9D9DCapstone Bonus: All threat generated is reduced by 30%.|r', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': 541591713},
)


arcane_meditation_11222 = spell(
    id=11222,
    name='Arcane Meditation',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=192),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=216),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=134),
    ],
    spell_icon_id=2894,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 0): repoints stock Arcane Focus\'s slot (id 76) to (0,1). "Increases spell, ranged and melee haste by 2/4/6%. Allows 25% of your mana regeneration to continue while casting." effect1 SPELL_AURA_MOD_MELEE_RANGED_HASTE (192), effect2 SPELL_AURA_HASTE_SPELLS (216), effect3 SPELL_AURA_MOD_MANA_REGEN_INTERRUPT (134, flat 25% every rank - the real stock mechanism, capped/applied directly by Player::UpdateManaRegen()). raw_overrides fully replaced (not merged) - the earlier version left stale classmask fields from Arcane Focus; caught and fixed.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell, ranged and melee haste by 2%. Allows 25% of your mana regeneration to continue while casting.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


arcane_stability_11237 = spell(
    id=11237,
    name='Arcane Stability',
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
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=306, misc_value=2048),
    ],
    spell_icon_id=225,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 0): retuned in place (same talent, same slot, tab 81 tier 0 col 2). "Increases your Proc Chance by 3/6/9%. Reduces spell pushback suffered from damaging attacks by 100%." effect1 (pushback, pre-existing SPELLMOD via apply_aura 108/misc_value 9, classmask-scoped to Arcane Missiles/Blast) retuned to a flat 100% on all 3 ranks (was 20/40/60/80/100% across 5 ranks - trimmed to 3, ranks 4/5\'s rows (16769/16770) left orphaned/unedited). effect2 is new: SPELL_AURA_MOD_CUSTOM_STAT_PCT (306), misc_value = 1<<CR_PROC_CHANCE (2048). Bugfix (playtest report, 2026-09-08): the Proc Chance clause was added as effect2 but never made it into the tooltip text - Description_Lang_enUS now states it explicitly, per rank.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Proc Chance by 3%. Reduces the pushback suffered from damaging attacks while casting Arcane Missiles and Arcane Blast by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 536872960, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


spell_impact_11242 = spell(
    id=11242,
    name='Spell Impact',
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
    ],
    spell_icon_id=122,
    notes="Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 1): retuned in place, same slot, moved from stock (2,1) to (1,2). Kept the existing correct classmask (EffectSpellClassMaskA_1 537006611 / _A_2 64 - Arcane Explosion, Arcane Blast, Blast Wave, Fire Blast, Scorch, Fireball, Ice Lance, Cone of Cold) rather than guessing at bits for the design doc's expanded list (Arcane Barrage, Arcane Orb, Arcane Overload, Pyroblast) - deferred to Phase 3/a follow-up data pass. Values retuned to 3/6/9% per the design doc.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Arcane Explosion, Arcane Blast, Arcane Barrage, Arcane Overload, Blast Wave, Fire Blast, Scorch, Pyroblast, Ice Lance and Cone of Cold spells by an additional $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 541200914, 'EffectSpellClassMaskA_2': 32832, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskA_3': 2},
)


arcane_concentration_11247 = spell(
    id=11247,
    name='Arcane Concentration',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=12536),
    ],
    spell_icon_id=212,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 2): repoints stock Magic Attunement\'s slot (id 82) to (2,0). "Gives you a 5/10/15% chance of entering a Clearcasting state after casting a damaging spell." effect1 SPELL_AURA_PROC_TRIGGER_SPELL (42) triggering the real stock Clearcasting buff (12536), ProcTypeMask 87376 ("damaging spell hits", same as the real stock Arcane Concentration talent) - proc chance is the spell\'s own ProcChance column, not an effect value. No classmask on the trigger itself (ProcTypeMask already scopes it; the real talent\'s own classmask appears to be additional narrowing not needed here). "...and increases its damage by your Mastery" NOT built this phase - needs a live Player::GetMasteryPercentage() read when Clearcasting is consumed, likely extending spell_mage_clearcasting; deferred to Phase 3. raw_overrides/effects fully replaced (not merged) - the earlier version left stale classmask fields from Magic Attunement; caught and fixed.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives you a 5% chance of entering a Clearcasting state after casting a damaging spell.', 'ProcChance': 5, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'ProcTypeMask': 87376},
)


arcane_shielding_11252 = spell(
    id=11252,
    name='Arcane Shielding',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=209,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 3): repoints stock Arcane Shielding\'s slot (id 83) to (3,0) - real content (Mana Shield/Mage Armor synergy) doesn\'t match this design, fully replaced. "Increases the amount absorbed by your Fire Ward, Frost Ward and Arcane Ward by 15/30%." "...your damage dealt is increased by 5/10% for 10 sec" on absorb built in Phase 3 (spell_mage_arcane_shielding_proc, spell_mage.cpp). Bugfix (2026-09-09, see docs/bugs-and-fixes.md "Missile Barrage\'s -50% still computed to -65%..."): effect1 used to be a classmask-scoped SPELLMOD_EFFECT1 (the only dword all three Wards share, 8, also happens to be part of Missile Barrage\'s (44401) own real family flags - a genuine, unfixable-by-relocating collision, not a wrong-slot mistake). Reimplemented as a plain SPELL_AURA_DUMMY marker (matching effect2\'s existing rank-lookup marker) read directly by a new DoEffectCalcAmount hook on spell_mage_arcane_shielding_proc (bound to 543/6143/28609/200068, same as its existing post-absorb damage-buff trigger) - no classmask involved at all, so no collision is possible.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount absorbed by your Fire Ward, Frost Ward and Arcane Ward by 15%. Each time one of these effects absorbs damage, your damage dealt is increased by 5% for 10 seconds.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


improved_counterspell_11255 = spell(
    id=11255,
    name='Improved Counterspell',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-5001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=17,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 3): repoints stock Improved Counterspell\'s slot (id 88) to (3,1) - real content (silence-on-cast proc only, no CD reduction) replaced. "Reduce the cooldown of your Counterspell ability by 5/10 seconds." effect1 SPELL_AURA_ADD_FLAT_MODIFIER (107)/SPELLMOD_COOLDOWN (11), EffectSpellClassMaskA_1 = 16384 (Counterspell, 2139 - verified live via the DB overlay) in raw_overrides. Capstone ("Counterspell now silences the target for 2 sec", rank 2) NOT built this phase - adds a wholly new effect to Counterspell, not expressible as a SpellMod; may also need a spell_proc/spell_proc_event row outside dbc-tools\' pipeline. Deferred to Phase 3. raw_overrides fully replaced (not merged) - the earlier version left a stale AttributesEx3 flag from the real silence-proc data; caught and fixed.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Counterspell ability by 5 seconds.\n\n|cFF9D9D9DCapstone Bonus: Your Counterspell ability now silences the target for 2 sec.|r', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': 16384},
)


critical_mass_11367 = spell(
    id=11367,
    name='Critical Mass',
    school=School.FIRE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=71, misc_value=4),
    ],
    spell_icon_id=117,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Fire spells by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 12582935, 'EffectSpellClassMaskA_2': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 2, 'SpellPriority': 50},
)


critical_mass_11368 = spell(
    id=11368,
    name='Critical Mass',
    school=School.FIRE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=71, misc_value=4),
    ],
    spell_icon_id=117,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Fire spells by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 12582935, 'EffectSpellClassMaskA_2': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 2, 'SpellPriority': 50},
)


improved_fireball_12338 = spell(
    id=12338,
    name='Improved Fireball',
    school=School.FIRE,
    attributes=262608,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=6, die_sides=0, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CRITICAL_CHANCE),
    ],
    spell_icon_id=185,
    notes='Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (0,2) rank 2: crit chance instead of the stock cast-time reduction; 3 ranks (ranks 4-5, 12340/12341, are no longer granted).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Fireball by 6%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


improved_fireball_12339 = spell(
    id=12339,
    name='Improved Fireball',
    school=School.FIRE,
    attributes=262608,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, die_sides=0, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CRITICAL_CHANCE),
    ],
    spell_icon_id=185,
    notes='Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (0,2) rank 3: crit chance instead of the stock cast-time reduction; 3 ranks (ranks 4-5, 12340/12341, are no longer granted).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Fireball by 9%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


improved_fireball_12340 = spell(
    id=12340,
    name='Improved Fireball',
    school=School.FIRE,
    attributes=262608,
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
    spell_icon_id=185,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the casting time of your Fireball spell by $/1000;S1 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskB_1': 1, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


improved_fireball_12341 = spell(
    id=12341,
    name='Improved Fireball',
    school=School.FIRE,
    attributes=262608,
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
    spell_icon_id=185,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the casting time of your Fireball spell by $/1000;S1 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskB_1': 1, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


world_in_flames_12349 = spell(
    id=12349,
    name='World in Flames',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=2948,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the critical strike chance of your Flamestrike, Pyroblast, Blast Wave, Dragon's Breath, Living Bomb, Blizzard and Arcane Explosion spells by $s1%.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 12587140, 'EffectSpellClassMaskA_2': 65600, 'EffectSpellClassMaskB_1': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


world_in_flames_12350 = spell(
    id=12350,
    name='World in Flames',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=2948,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the critical strike chance of your Flamestrike, Pyroblast, Blast Wave, Dragon's Breath, Living Bomb, Blizzard and Arcane Explosion spells by $s1%.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 12587140, 'EffectSpellClassMaskA_2': 65600, 'EffectSpellClassMaskB_1': 4, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


burning_soul_12351 = spell(
    id=12351,
    name='Burning Soul',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.NOT_LOSE_CASTING_TIME),
        Effect(type=EffectType.APPLY_AURA, base_points=2, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MOD_SPELL_CRIT_CHANCE),
    ],
    spell_icon_id=11,
    notes='Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (0,3) rank 2: pushback reduction to 100% at every rank (still scoped to Fire spells via the stock classmask on Effect_1), threat reduction replaced by flat spell crit. Rank 3 is new (200102).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell critical strike chance by 2%. Reduces spell pushback suffered from damaging attacks by 100%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194325, 'EffectSpellClassMaskA_2': 4096, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


flame_throwing_12353 = spell(
    id=12353,
    name='Flame Throwing',
    school=School.FIRE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.RANGE),
        Effect(type=EffectType.APPLY_AURA, base_points=-19, die_sides=0, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.CASTING_TIME),
    ],
    spell_icon_id=136,
    notes="Fire Mage rework Phase 3 (2,0) rank 2: EFFECT_1 is the capstone's live cast-time reduction, scoped to Fireball alone (EffectSpellClassMaskB_1=1, letter B = effect index 1). base_points -19 -> real value -20% (die_sides=1 convention). spell_mage_flame_throwing_capstone's DoEffectCalcAmount overrides this to 0 while the 12s lockout (200112) is up, via AuraEffect::RecalculateAmount() triggered by spell_mage_fireball whenever the lockout applies/expires - see that script's own comment for why a cached SpellModifier value needs an explicit recalculation trigger, unlike a live-read DUMMY marker.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of all Fire spells except Frostfire Bolt by 6 yards.\n\nCapstone Bonus: The cast time of your Fireball is reduced by 20%. This effect becomes inactive for 12 sec after use.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194327, 'EffectSpellClassMaskA_2': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskB_1': 1},
)


impact_12357 = spell(
    id=12357,
    name='Impact',
    school=School.FIRE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=64343),
    ],
    spell_icon_id=45,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 136, 'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your damaging spells a $h% chance to cause the next Fire Blast you cast to stun the target for $12355d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 7, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


impact_12358 = spell(
    id=12358,
    name='Impact',
    school=School.FIRE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=64343),
    ],
    spell_icon_id=45,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 136, 'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your damaging spells a $h% chance to cause the next Fire Blast you cast to stun the target for $12355d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 10, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


fire_power_12378 = spell(
    id=12378,
    name='Fire Power',
    school=School.FIRE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=31,
    notes='Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (5,2) rank 2: 3 ranks (was 5), 6%. Ranks 4-5 (12399/12400) are no longer granted.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Fire spells by 6%.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 12845079, 'EffectSpellClassMaskA_2': 69704, 'EffectSpellClassMaskB_1': 4194309, 'EffectSpellClassMaskB_2': 135168, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


fire_power_12398 = spell(
    id=12398,
    name='Fire Power',
    school=School.FIRE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=31,
    notes='Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (5,2) rank 3: 3 ranks (was 5), 10%. Ranks 4-5 (12399/12400) are no longer granted.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Fire spells by 10%.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 12845079, 'EffectSpellClassMaskA_2': 69704, 'EffectSpellClassMaskB_1': 4194309, 'EffectSpellClassMaskB_2': 135168, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


fire_power_12399 = spell(
    id=12399,
    name='Fire Power',
    school=School.FIRE,
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
    spell_icon_id=31,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Fire spells by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 12845079, 'EffectSpellClassMaskA_2': 69704, 'EffectSpellClassMaskB_1': 4194309, 'EffectSpellClassMaskB_2': 135168, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


fire_power_12400 = spell(
    id=12400,
    name='Fire Power',
    school=School.FIRE,
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
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Fire spells by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 12845079, 'EffectSpellClassMaskA_2': 69704, 'EffectSpellClassMaskB_1': 4194309, 'EffectSpellClassMaskB_2': 135168, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


arcane_stability_12463 = spell(
    id=12463,
    name='Arcane Stability',
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
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=306, misc_value=2048),
    ],
    spell_icon_id=225,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 0): retuned in place (same talent, same slot, tab 81 tier 0 col 2). "Increases your Proc Chance by 3/6/9%. Reduces spell pushback suffered from damaging attacks by 100%." effect1 (pushback, pre-existing SPELLMOD via apply_aura 108/misc_value 9, classmask-scoped to Arcane Missiles/Blast) retuned to a flat 100% on all 3 ranks (was 20/40/60/80/100% across 5 ranks - trimmed to 3, ranks 4/5\'s rows (16769/16770) left orphaned/unedited). effect2 is new: SPELL_AURA_MOD_CUSTOM_STAT_PCT (306), misc_value = 1<<CR_PROC_CHANCE (2048).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Proc Chance by 6%. Reduces the pushback suffered from damaging attacks while casting Arcane Missiles and Arcane Blast by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 536872960, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


arcane_stability_12464 = spell(
    id=12464,
    name='Arcane Stability',
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
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=306, misc_value=2048),
    ],
    spell_icon_id=225,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 0): retuned in place (same talent, same slot, tab 81 tier 0 col 2). "Increases your Proc Chance by 3/6/9%. Reduces spell pushback suffered from damaging attacks by 100%." effect1 (pushback, pre-existing SPELLMOD via apply_aura 108/misc_value 9, classmask-scoped to Arcane Missiles/Blast) retuned to a flat 100% on all 3 ranks (was 20/40/60/80/100% across 5 ranks - trimmed to 3, ranks 4/5\'s rows (16769/16770) left orphaned/unedited). effect2 is new: SPELL_AURA_MOD_CUSTOM_STAT_PCT (306), misc_value = 1<<CR_PROC_CHANCE (2048).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Proc Chance by 9%. Reduces the pushback suffered from damaging attacks while casting Arcane Missiles and Arcane Blast by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 536872960, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


spell_impact_12467 = spell(
    id=12467,
    name='Spell Impact',
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
    ],
    spell_icon_id=122,
    notes="Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 1): retuned in place, same slot, moved from stock (2,1) to (1,2). Kept the existing correct classmask (EffectSpellClassMaskA_1 537006611 / _A_2 64 - Arcane Explosion, Arcane Blast, Blast Wave, Fire Blast, Scorch, Fireball, Ice Lance, Cone of Cold) rather than guessing at bits for the design doc's expanded list (Arcane Barrage, Arcane Orb, Arcane Overload, Pyroblast) - deferred to Phase 3/a follow-up data pass. Values retuned to 3/6/9% per the design doc.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Arcane Explosion, Arcane Blast, Arcane Barrage, Arcane Overload, Blast Wave, Fire Blast, Scorch, Pyroblast, Ice Lance and Cone of Cold spells by an additional $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 541200914, 'EffectSpellClassMaskA_2': 32832, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskA_3': 2},
)


spell_impact_12469 = spell(
    id=12469,
    name='Spell Impact',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=122,
    notes="Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 1): retuned in place, same slot, moved from stock (2,1) to (1,2). Kept the existing correct classmask (EffectSpellClassMaskA_1 537006611 / _A_2 64 - Arcane Explosion, Arcane Blast, Blast Wave, Fire Blast, Scorch, Fireball, Ice Lance, Cone of Cold) rather than guessing at bits for the design doc's expanded list (Arcane Barrage, Arcane Orb, Arcane Overload, Pyroblast) - deferred to Phase 3/a follow-up data pass. Values retuned to 3/6/9% per the design doc.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Arcane Explosion, Arcane Blast, Arcane Barrage, Arcane Overload, Blast Wave, Fire Blast, Scorch, Pyroblast, Ice Lance and Cone of Cold spells by an additional $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 541200914, 'EffectSpellClassMaskA_2': 32832, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskA_3': 2},
)


improved_frostbolt_12473 = spell(
    id=12473,
    name='Improved Frostbolt',
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
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=188,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Frostbolt and Ice Lance spells by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 131104, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


improved_blizzard_12487 = spell(
    id=12487,
    name='Improved Blizzard',
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
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=112, misc_value=988),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=108, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=108, misc_value=19),
    ],
    spell_icon_id=285,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Adds a chill effect to your Blizzard spell.  This effect lowers the target's movement speed by $12484s1%.  Lasts $12484d.  Also reduces the mana cost of Blizzard by $s2% and its periodic interval by $s3%.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 128, 'EffectSpellClassMaskA_1': 128, 'EffectSpellClassMaskA_2': 524416, 'EffectSpellClassMaskA_3': 524416, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


improved_blizzard_12488 = spell(
    id=12488,
    name='Improved Blizzard',
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
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=112, misc_value=989),
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=108, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=-29, implicit_target_a=1, apply_aura=108, misc_value=19),
    ],
    spell_icon_id=285,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Adds a chill effect to your Blizzard spell.  This effect lowers the target's movement speed by $12484s1%.  Lasts $12484d.  Also reduces the mana cost of Blizzard by $s2% and its periodic interval by $s3%.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 128, 'EffectSpellClassMaskA_1': 128, 'EffectSpellClassMaskA_2': 524416, 'EffectSpellClassMaskA_3': 524416, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


improved_cone_of_cold_12489 = spell(
    id=12489,
    name='Improved Cone of Cold',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=74396),
    ],
    spell_icon_id=35,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 6, Improved Cone of Cold). effect1 (dmg%) kept the pulled data's mechanic/scope (ADD_PCT_MODIFIER, SPELLMOD_DAMAGE, classmask already Cone-of-Cold-only) but retuned 14/24/34 -> 19/39/59 (stored+1 = 20/40/60%, spec's value; old data was a stale/different tuning). effect2 (new, all 3 ranks): FoF-chance-on-hit, same shape as Improved Blizzard's own FoF grant -- native PROC_TRIGGER_SPELL straight to the Fingers of Frost charge spell (74396), 33/66/100% (literal, not stored+1 -- ProcChance convention). ",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage dealt by your Cone of Cold spell by $s1%, and gives it a $h% chance to grant Fingers of Frost. |cFF9D9D9DAt max rank, after casting Cone of Cold, your Blizzard channels twice as fast.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 512, 'EffectSpellClassMaskA_1': 512, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 66, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'ProcTypeMask': 65536, 'EffectSpellClassMaskA_2': 512},
)


improved_cone_of_cold_12490 = spell(
    id=12490,
    name='Improved Cone of Cold',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=59, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=74396),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200020),
    ],
    spell_icon_id=35,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 6, Improved Cone of Cold). effect1 (dmg%) kept the pulled data's mechanic/scope (ADD_PCT_MODIFIER, SPELLMOD_DAMAGE, classmask already Cone-of-Cold-only) but retuned 14/24/34 -> 19/39/59 (stored+1 = 20/40/60%, spec's value; old data was a stale/different tuning). effect2 (new, all 3 ranks): FoF-chance-on-hit, same shape as Improved Blizzard's own FoF grant -- native PROC_TRIGGER_SPELL straight to the Fingers of Frost charge spell (74396), 33/66/100% (literal, not stored+1 -- ProcChance convention). effect3 (rank 3 only, capstone): 'your Blizzard channels twice as fast' after casting Cone of Cold -- a new buff (200020, ADD_PCT_MODIFIER/SPELLMOD_ACTIVATION_TIME -50%, classmask Blizzard-only, ProcCharges=1) auto-consumed by the native SpellMod charge system on the next Blizzard cast (Player::ApplySpellMod's charge-consumption path, no script needed) -- duration window (15 sec) is a first-pass assumption since the redesign text doesn't give one, flagged for playtest.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage dealt by your Cone of Cold spell by $s1%, and gives it a $h% chance to grant Fingers of Frost. After casting Cone of Cold, your Blizzard channels twice as fast.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectItemType_1': 512, 'EffectSpellClassMaskA_1': 512, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'ProcTypeMask': 65536, 'EffectSpellClassMaskA_2': 512, 'EffectSpellClassMaskA_3': 512},
)


frostbite_12496 = spell(
    id=12496,
    name='Frostbite',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=12494),
    ],
    spell_icon_id=119,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Dealing direct Frost damage has a $s1% chance to freeze the target for $12494d.  The freeze breaks on damage.\n\n|cFF9D9D9DCapstone Bonus: Increases the damage of your Frost spells against frozen targets based on your Mastery.|r', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_2': 4096, 'EffectSpellClassMaskB_2': 4096, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 10, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassMask_2': 512, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


frostbite_12497 = spell(
    id=12497,
    name='Frostbite',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=12494),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=119,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Dealing direct Frost damage has a $s1% chance to freeze the target for $12494d.  The freeze breaks on damage.\n\nCapstone Bonus: Increases the damage of your Frost spells against frozen targets based on your Mastery.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_2': 4096, 'EffectSpellClassMaskB_2': 4096, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 15, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassMask_2': 512, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


frost_channeling_12518 = spell(
    id=12518,
    name='Frost Channeling',
    school=School.FROST,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-9, implicit_target_a=1, apply_aura=72, misc_value=16),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=AuraType.MOD_THREAT, misc_value=16),
    ],
    spell_icon_id=15,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your Frost spells and abilities by $s1% and reduces the threat caused by $s2%. |cFF9D9D9DAt max rank, killing an enemy that yields experience or honor with Frost damage restores 12% of your mana.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 1, 'EffectSpellClassMaskA_1': 655360, 'EffectSpellClassMaskA_2': 2049, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


frost_channeling_12519 = spell(
    id=12519,
    name='Frost Channeling',
    school=School.FROST,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-13, implicit_target_a=1, apply_aura=72, misc_value=16),
        Effect(type=EffectType.APPLY_AURA, base_points=-16, implicit_target_a=1, apply_aura=AuraType.MOD_THREAT, misc_value=16),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=15,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your Frost spells and abilities by $s1% and reduces the threat caused by $s2%.  Killing an enemy that yields experience or honor with Frost damage restores 12% of your mana.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 1, 'EffectSpellClassMaskA_1': 655360, 'EffectSpellClassMaskA_2': 2049, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


permafrost_12569 = spell(
    id=12569,
    name='Permafrost',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1999, implicit_target_a=1, apply_aura=107, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=-8, implicit_target_a=1, apply_aura=107, misc_value=3),
    ],
    spell_icon_id=143,
    notes='Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 2, Permafrost). Base effect kept the pulled data\'s own numbers (already matched spec\'s 1/2/3 sec duration + 4/7/10% additional slow via the stored+1 convention) but rescoped from the old talent\'s actual shape -- a target-side debuff (duration/slow/heal-received-reduction applied to whoever the mage\'s Frostbolt/Cone of Cold/Frost Nova hit) -- to a caster-side SpellMod pair (SPELLMOD_DURATION + SPELLMOD_EFFECT1, classmask 544 = Frostbolt|Cone of Cold in word A) boosting the caster\'s own cast of those spells, matching every other \'duration+value modifier\' talent this project has built (Arctic Reach, Chilled to the Bone). The old effect3 (SPELLMOD_EFFECT3, -8/-14/-21, confirmed via the Chilled npc-caster spells 6136/7321\'s own effect3 = SPELL_AURA_MOD_HEALING_PCT to be the dropped tooltip\'s \'reduces healing received\' clause) is not in the new spec and was removed outright, not carried forward. \'Frost Shock\' in the redesign\'s talent text was dropped per user decision (2026-08-24) -- not a real Mage spell (Shaman-only in this game), most likely a stray copy-paste word; scoped to Cone of Cold/Frostbolt/Ice Armor only. Ice Armor\'s own melee-reactive slow (6136 Frost Armor / 7321 Ice Armor\'s \'Chilled\' trigger spells, npc.csv) has no SpellFamilyFlags of its own -- same classmask-unreachable shape as Frozen Orb hit this project before -- so it\'s boosted live in spell_mage_chilled (spell_mage.cpp) instead, same \'read the mage\'s own SpellMod amount and fold it in\' idiom as spell_mage_frozen_orb_pulse\'s Chilled to the Bone fix. Capstone (rank 3 only): see effect3. Playtest bugfix (2026-08-27, user report - "Permafrost reduces the effects of everything by 10%, not just move speed"): the SPELLMOD_EFFECT1 modifier\'s classmask (544, Frostbolt|Cone of Cold) was stored under EffectSpellClassMaskA_2, which the naming convention suggests is "effect index 2\'s word A" but which spell_dbc/DBCStructure.h actually reads as "effect index 0(=A)\'s word 2" - dword-major, not effect-major, unlike every other _1/_2/_3-suffixed field in this schema. That left the real target, effect index 1\'s own classmask, all-zero, and SpellInfo::IsAffected treats an all-zero classmask as matching every spell in the family - so the -4/-7/-10% modifier applied unconditionally to EFFECT_0 of every mage spell (including Evocation\'s mana-restore %) instead of just Frostbolt/Cone of Cold. Fixed by moving the value to EffectSpellClassMaskB_1 (effect index 1(=B)\'s word 1), which is what the engine actually reads for effect 1\'s classmask. See data/sql/updates/pending_db_world/frost_mage_rework.sql (merged Frost Mage rework migration; originally rev_1787820084006262155.sql) for the original diagnosis (that migration was a live DB-only patch of the affected rows; this is the matching source-of-truth fix so future full regenerations don\'t reintroduce it).',
    raw_overrides={'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the duration of your Cone of Cold and Frostbolt slow effects by ${{$m1/1000}}.1 sec, and reduces the target's speed by an additional $s2%. Also affects Ice Armor's chilling effect. |cFF9D9D9DAt max rank: each 1 sec you spend moving grants Permafrost, increasing the damage of your next Ice Lance by 20%. Stacks up to 5 times.|r", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 544, 'EffectSpellClassMaskB_1': 544, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


permafrost_12571 = spell(
    id=12571,
    name='Permafrost',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2999, implicit_target_a=1, apply_aura=107, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=107, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=226, amplitude=1000),
    ],
    spell_icon_id=143,
    notes='Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 2, Permafrost). Base effect kept the pulled data\'s own numbers (already matched spec\'s 1/2/3 sec duration + 4/7/10% additional slow via the stored+1 convention) but rescoped from the old talent\'s actual shape -- a target-side debuff (duration/slow/heal-received-reduction applied to whoever the mage\'s Frostbolt/Cone of Cold/Frost Nova hit) -- to a caster-side SpellMod pair (SPELLMOD_DURATION + SPELLMOD_EFFECT1, classmask 544 = Frostbolt|Cone of Cold in word A) boosting the caster\'s own cast of those spells, matching every other \'duration+value modifier\' talent this project has built (Arctic Reach, Chilled to the Bone). The old effect3 (SPELLMOD_EFFECT3, -8/-14/-21, confirmed via the Chilled npc-caster spells 6136/7321\'s own effect3 = SPELL_AURA_MOD_HEALING_PCT to be the dropped tooltip\'s \'reduces healing received\' clause) is not in the new spec and was removed outright, not carried forward. \'Frost Shock\' in the redesign\'s talent text was dropped per user decision (2026-08-24) -- not a real Mage spell (Shaman-only in this game), most likely a stray copy-paste word; scoped to Cone of Cold/Frostbolt/Ice Armor only. Ice Armor\'s own melee-reactive slow (6136 Frost Armor / 7321 Ice Armor\'s \'Chilled\' trigger spells, npc.csv) has no SpellFamilyFlags of its own -- same classmask-unreachable shape as Frozen Orb hit this project before -- so it\'s boosted live in spell_mage_chilled (spell_mage.cpp) instead, same \'read the mage\'s own SpellMod amount and fold it in\' idiom as spell_mage_frozen_orb_pulse\'s Chilled to the Bone fix. Capstone (rank 3 only): see effect3. Playtest bugfix (2026-08-27, user report - "Permafrost reduces the effects of everything by 10%, not just move speed"): the SPELLMOD_EFFECT1 modifier\'s classmask (544, Frostbolt|Cone of Cold) was stored under EffectSpellClassMaskA_2, which the naming convention suggests is "effect index 2\'s word A" but which spell_dbc/DBCStructure.h actually reads as "effect index 0(=A)\'s word 2" - dword-major, not effect-major, unlike every other _1/_2/_3-suffixed field in this schema. That left the real target, effect index 1\'s own classmask, all-zero, and SpellInfo::IsAffected treats an all-zero classmask as matching every spell in the family - so the -4/-7/-10% modifier applied unconditionally to EFFECT_0 of every mage spell (including Evocation\'s mana-restore %) instead of just Frostbolt/Cone of Cold. Fixed by moving the value to EffectSpellClassMaskB_1 (effect index 1(=B)\'s word 1), which is what the engine actually reads for effect 1\'s classmask. See data/sql/updates/pending_db_world/frost_mage_rework.sql (merged Frost Mage rework migration; originally rev_1787820084006262155.sql) for the original diagnosis (that migration was a live DB-only patch of the affected rows; this is the matching source-of-truth fix so future full regenerations don\'t reintroduce it).',
    raw_overrides={'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the duration of your Cone of Cold and Frostbolt slow effects by ${{$m1/1000}}.1 sec, and reduces the target's speed by an additional $s2%. Also affects Ice Armor's chilling effect. Each 1 sec you spend moving grants Permafrost, increasing the damage of your next Ice Lance by 20%. Stacks up to 5 times.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 544, 'EffectSpellClassMaskB_1': 544, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


arcane_subtlety_12574 = spell(
    id=12574,
    name='Arcane Subtlety',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=107, misc_value=5),
        Effect(type=EffectType.APPLY_AURA, base_points=-9, implicit_target_a=1, apply_aura=72, misc_value=64),
    ],
    spell_icon_id=74,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 1): repoints stock Arcane Concentration\'s slot (id 75) to (1,1), trimmed to 3 ranks. "Increases the range of your damaging spells with a channeling or cast time by 2/4/6 yards." effect1 SPELL_AURA_ADD_FLAT_MODIFIER (107)/SPELLMOD_RANGE (5), EffectSpellClassMaskA_1 (raw_override, NOT the friendly effect misc_value) covering Frostbolt|Fireball|Arcane Blast|Blizzard|Pyroblast|Arcane Missiles - individually verified live via the DB overlay; not exhaustive (Frostfire Bolt, Cone of Cold, a few others not yet verified), flagged for a follow-up data pass. "Reduces the mana cost of your Arcane Spells by 4/8/12%" - effect2 SPELL_AURA_MOD_POWER_COST_SCHOOL_PCT (72), misc_value 64 (Arcane school, not classmask - no scoping risk). Capstone (rank 3 only, "threat reduced by 30%") - effect3 SPELL_AURA_MOD_THREAT (10), misc_value 64. Corrected from an earlier broken version of this edit: the range effect\'s classmask was accidentally written into the friendly effect1 JSON blob instead of raw_overrides (silently ignored there), and stale trigger_spell/classmask/attribute fields from the real Arcane Concentration data this slot used to hold survived a merge instead of being cleared - both caught by generate.py\'s lint WARNING and fixed here with a full (non-merging) rewrite.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of your damaging spells with a channeling or cast time by 4 yards. Reduces the mana cost of your Arcane Spells by 8%.\n\n|cFF9D9D9DCapstone Bonus: All threat generated is reduced by 30%.|r', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': 541591713},
)


arcane_subtlety_12575 = spell(
    id=12575,
    name='Arcane Subtlety',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=107, misc_value=5),
        Effect(type=EffectType.APPLY_AURA, base_points=-13, implicit_target_a=1, apply_aura=72, misc_value=64),
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=AuraType.MOD_THREAT, misc_value=64),
    ],
    spell_icon_id=74,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 1): repoints stock Arcane Concentration\'s slot (id 75) to (1,1), trimmed to 3 ranks. "Increases the range of your damaging spells with a channeling or cast time by 2/4/6 yards." effect1 SPELL_AURA_ADD_FLAT_MODIFIER (107)/SPELLMOD_RANGE (5), EffectSpellClassMaskA_1 (raw_override, NOT the friendly effect misc_value) covering Frostbolt|Fireball|Arcane Blast|Blizzard|Pyroblast|Arcane Missiles - individually verified live via the DB overlay; not exhaustive (Frostfire Bolt, Cone of Cold, a few others not yet verified), flagged for a follow-up data pass. "Reduces the mana cost of your Arcane Spells by 4/8/12%" - effect2 SPELL_AURA_MOD_POWER_COST_SCHOOL_PCT (72), misc_value 64 (Arcane school, not classmask - no scoping risk). Capstone (rank 3 only, "threat reduced by 30%") - effect3 SPELL_AURA_MOD_THREAT (10), misc_value 64. Corrected from an earlier broken version of this edit: the range effect\'s classmask was accidentally written into the friendly effect1 JSON blob instead of raw_overrides (silently ignored there), and stale trigger_spell/classmask/attribute fields from the real Arcane Concentration data this slot used to hold survived a merge instead of being cleared - both caught by generate.py\'s lint WARNING and fixed here with a full (non-merging) rewrite.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of your damaging spells with a channeling or cast time by 6 yards. Reduces the mana cost of your Arcane Spells by 12%.\n\nCapstone Bonus: All threat generated is reduced by 30%.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': 541591713},
)


arcane_concentration_12576 = spell(
    id=12576,
    name='Arcane Concentration',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=12536),
    ],
    spell_icon_id=212,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 8388608, 'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives you a $h% chance of entering a Clearcasting state after any damage spell hits a target.  The Clearcasting state reduces the mana cost of your next damage spell by $/10;12536s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 128, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 8, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


arcane_concentration_12577 = spell(
    id=12577,
    name='Arcane Concentration',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=12536),
    ],
    spell_icon_id=212,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 8388608, 'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives you a $h% chance of entering a Clearcasting state after any damage spell hits a target.  The Clearcasting state reduces the mana cost of your next damage spell by $/10;12536s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 128, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 10, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


alacrity_12592 = spell(
    id=12592,
    name='Alacrity',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=306, misc_value=4194304),
    ],
    spell_icon_id=2022,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 0): repoints stock Arcane Subtlety\'s slot (id 74) to (0,0). "Increases your cooldown reduction by 5/10/15%." SPELL_AURA_MOD_CUSTOM_STAT_PCT (306), misc_value 1<<CR_COOLDOWN_HASTE (4194304). raw_overrides fully replaced (not merged) - the earlier version of this edit left stale classmask/attribute fields from the real Arcane Subtlety talent this slot used to hold; caught and fixed.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Cooldown Haste by 10%.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


improved_counterspell_12598 = spell(
    id=12598,
    name='Improved Counterspell',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-10001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=17,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 3): repoints stock Improved Counterspell\'s slot (id 88) to (3,1) - real content (silence-on-cast proc only, no CD reduction) replaced. "Reduce the cooldown of your Counterspell ability by 5/10 seconds." effect1 SPELL_AURA_ADD_FLAT_MODIFIER (107)/SPELLMOD_COOLDOWN (11), EffectSpellClassMaskA_1 = 16384 (Counterspell, 2139 - verified live via the DB overlay) in raw_overrides. Capstone ("Counterspell now silences the target for 2 sec", rank 2) NOT built this phase - adds a wholly new effect to Counterspell, not expressible as a SpellMod; may also need a spell_proc/spell_proc_event row outside dbc-tools\' pipeline. Deferred to Phase 3. raw_overrides fully replaced (not merged) - the earlier version left a stale AttributesEx3 flag from the real silence-proc data; caught and fixed.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Counterspell ability by 10 seconds.\n\nCapstone Bonus: Your Counterspell ability now silences the target for 2 sec.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': 16384},
)


arcane_shielding_12605 = spell(
    id=12605,
    name='Arcane Shielding',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=209,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 3): repoints stock Arcane Shielding\'s slot (id 83) to (3,0) - real content (Mana Shield/Mage Armor synergy) doesn\'t match this design, fully replaced. "Increases the amount absorbed by your Fire Ward, Frost Ward and Arcane Ward by 15/30%." "...your damage dealt is increased by 5/10% for 10 sec" on absorb built in Phase 3 (spell_mage_arcane_shielding_proc, spell_mage.cpp). Bugfix (2026-09-09, see docs/bugs-and-fixes.md "Missile Barrage\'s -50% still computed to -65%..."): effect1 used to be a classmask-scoped SPELLMOD_EFFECT1 (the only dword all three Wards share, 8, also happens to be part of Missile Barrage\'s (44401) own real family flags - a genuine, unfixable-by-relocating collision, not a wrong-slot mistake). Reimplemented as a plain SPELL_AURA_DUMMY marker (matching effect2\'s existing rank-lookup marker) read directly by a new DoEffectCalcAmount hook on spell_mage_arcane_shielding_proc (bound to 543/6143/28609/200068, same as its existing post-absorb damage-buff trigger) - no classmask involved at all, so no collision is possible.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the amount absorbed by your Fire Ward, Frost Ward and Arcane Ward by 30%. Each time one of these effects absorbs damage, your damage dealt is increased by 10% for 10 seconds.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


arcane_concentration_12606 = spell(
    id=12606,
    name='Arcane Concentration',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=12536),
    ],
    spell_icon_id=212,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 2): repoints stock Magic Attunement\'s slot (id 82) to (2,0). "Gives you a 5/10/15% chance of entering a Clearcasting state after casting a damaging spell." effect1 SPELL_AURA_PROC_TRIGGER_SPELL (42) triggering the real stock Clearcasting buff (12536), ProcTypeMask 87376 ("damaging spell hits", same as the real stock Arcane Concentration talent) - proc chance is the spell\'s own ProcChance column, not an effect value. No classmask on the trigger itself (ProcTypeMask already scopes it; the real talent\'s own classmask appears to be additional narrowing not needed here). "...and increases its damage by your Mastery" NOT built this phase - needs a live Player::GetMasteryPercentage() read when Clearcasting is consumed, likely extending spell_mage_clearcasting; deferred to Phase 3. raw_overrides/effects fully replaced (not merged) - the earlier version left stale classmask fields from Magic Attunement; caught and fixed.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives you a 10% chance of entering a Clearcasting state after casting a damaging spell.', 'ProcChance': 10, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'ProcTypeMask': 87376},
)


ice_shards_12672 = spell(
    id=12672,
    name='Ice Shards',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=69, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=1236,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of your Frost spells by $s1%. |cFF9D9D9DAt max rank, increases damage against frozen targets by 6%.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 131808, 'EffectSpellClassMaskA_2': 1052672, 'EffectSpellClassMaskA_3': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


arcane_meditation_12839 = spell(
    id=12839,
    name='Arcane Meditation',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=192),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=216),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=134),
    ],
    spell_icon_id=2894,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 0): repoints stock Arcane Focus\'s slot (id 76) to (0,1). "Increases spell, ranged and melee haste by 2/4/6%. Allows 25% of your mana regeneration to continue while casting." effect1 SPELL_AURA_MOD_MELEE_RANGED_HASTE (192), effect2 SPELL_AURA_HASTE_SPELLS (216), effect3 SPELL_AURA_MOD_MANA_REGEN_INTERRUPT (134, flat 25% every rank - the real stock mechanism, capped/applied directly by Player::UpdateManaRegen()). raw_overrides fully replaced (not merged) - the earlier version left stale classmask fields from Arcane Focus; caught and fixed.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell, ranged and melee haste by 4%. Allows 25% of your mana regeneration to continue while casting.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


arcane_meditation_12840 = spell(
    id=12840,
    name='Arcane Meditation',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=192),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=216),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=134),
    ],
    spell_icon_id=2894,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 0): repoints stock Arcane Focus\'s slot (id 76) to (0,1). "Increases spell, ranged and melee haste by 2/4/6%. Allows 25% of your mana regeneration to continue while casting." effect1 SPELL_AURA_MOD_MELEE_RANGED_HASTE (192), effect2 SPELL_AURA_HASTE_SPELLS (216), effect3 SPELL_AURA_MOD_MANA_REGEN_INTERRUPT (134, flat 25% every rank - the real stock mechanism, capped/applied directly by Player::UpdateManaRegen()). raw_overrides fully replaced (not merged) - the earlier version left stale classmask fields from Arcane Focus; caught and fixed.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell, ranged and melee haste by 6%. Allows 25% of your mana regeneration to continue while casting.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


ignite_12846 = spell(
    id=12846,
    name='Ignite',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=50, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=937,
    notes='Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (1,0) rank 3: 3 ranks (was 5), percentage rescaled to 50; EFFECT_0 DUMMY carries it for spell_mage_ignite / Mage::AddIgniteDamage. Ranks 4-5 (12847/12848) are no longer granted.',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your critical strikes from Fire damage spells cause the target to burn for an additional 50% of your spell's damage over $12654d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 327680, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


ignite_12847 = spell(
    id=12847,
    name='Ignite',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=32, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=937,
    notes='Fire Mage rework Phase 1: EFFECT_0 DUMMY now carries the live Ignite percentage (32, die_sides 0 so GetAmount() is exact) so spell_mage_ignite reads it instead of hardcoding 8 * GetRank() - see Mage::AddIgniteDamage. Value unchanged from stock for this rank.',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your critical strikes from Fire damage spells cause the target to burn for an additional 32% of your spell's damage over $12654d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 327680, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


ignite_12848 = spell(
    id=12848,
    name='Ignite',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=40, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=937,
    notes='Fire Mage rework Phase 1: EFFECT_0 DUMMY now carries the live Ignite percentage (40, die_sides 0 so GetAmount() is exact) so spell_mage_ignite reads it instead of hardcoding 8 * GetRank() - see Mage::AddIgniteDamage. Value unchanged from stock for this rank.',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your critical strikes from Fire damage spells cause the target to burn for an additional 40% of your spell's damage over $12654d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 134217728, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 327680, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


improved_scorch_12872 = spell(
    id=12872,
    name='Improved Scorch',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=22959),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=816,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your chance to critically hit with Scorch, Fireball and Frostfire Bolt by an additional $s2% and your damaging Scorch spells have a $h% chance to cause your target to be vulnerable to spell damage, increasing spell critical strike chance against that target by $22959s1% and lasts $22959d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 16, 'EffectSpellClassMaskB_1': 17, 'EffectSpellClassMaskB_2': 4096, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 66, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellPriority': 50},
)


improved_scorch_12873 = spell(
    id=12873,
    name='Improved Scorch',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=22959),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=816,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your chance to critically hit with Scorch, Fireball and Frostfire Bolt by an additional $s2% and your damaging Scorch spells have a $h% chance to cause your target to be vulnerable to spell damage, increasing spell critical strike chance against that target by $22959s1% and lasts $22959d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 16, 'EffectSpellClassMaskB_1': 17, 'EffectSpellClassMaskB_2': 4096, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellPriority': 50},
)


piercing_ice_12952 = spell(
    id=12952,
    name='Piercing Ice',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=79, misc_value=16),
    ],
    spell_icon_id=176,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Frost spells by $s1%.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 131808, 'EffectSpellClassMaskB_1': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


piercing_ice_12953 = spell(
    id=12953,
    name='Piercing Ice',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=79, misc_value=16),
    ],
    spell_icon_id=176,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Frost spells by $s1%.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 131808, 'EffectSpellClassMaskB_1': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


shatter_12982 = spell(
    id=12982,
    name='Shatter',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=112, misc_value=910),
    ],
    spell_icon_id=976,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of all your spells against frozen targets by 34%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 552211063, 'EffectSpellClassMaskA_2': 1151048, 'EffectSpellClassMaskA_3': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


shatter_12983 = spell(
    id=12983,
    name='Shatter',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=112, misc_value=911),
    ],
    spell_icon_id=976,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of all your spells against frozen targets by 50%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 552211063, 'EffectSpellClassMaskA_2': 1151048, 'EffectSpellClassMaskA_3': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


molten_shields_13043 = spell(
    id=13043,
    name='Molten Shields',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=107, misc_value=12),
    ],
    spell_icon_id=16,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes your Fire Ward and Frost Ward spells to have a $s1% chance to reflect the warded spell while active. In addition, your Molten Armor has a 100% chance to affect ranged and spell attacks.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 264, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


ice_shards_15047 = spell(
    id=15047,
    name='Ice Shards',
    school=School.FROST,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=108, misc_value=15),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1236,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of your Frost spells by $s1%.  Increases damage against frozen targets by 6%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 131808, 'EffectSpellClassMaskA_2': 1052672, 'EffectSpellClassMaskA_3': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


arcane_instability_15058 = spell(
    id=15058,
    name='Arcane Instability',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=79, misc_value=64),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=71, misc_value=127),
    ],
    spell_icon_id=87,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your spells and your critical strike chance by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 14947063, 'EffectSpellClassMaskB_1': 4194437, 'EffectSpellClassMaskC_1': 14684919, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3},
)


arcane_instability_15059 = spell(
    id=15059,
    name='Arcane Instability',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=79, misc_value=64),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=71, misc_value=127),
    ],
    spell_icon_id=87,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your spells and your critical strike chance by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 14947063, 'EffectSpellClassMaskB_1': 4194437, 'EffectSpellClassMaskC_1': 14684919, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3},
)


arcane_instability_15060 = spell(
    id=15060,
    name='Arcane Instability',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=79, misc_value=64),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=71, misc_value=127),
    ],
    spell_icon_id=87,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your spells and your critical strike chance by $s1%.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 14947063, 'EffectSpellClassMaskB_1': 4194437, 'EffectSpellClassMaskC_1': 14684919, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3},
)


arctic_reach_16757 = spell(
    id=16757,
    name='Arctic Reach',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=107, misc_value=5),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=6),
    ],
    spell_icon_id=154,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the range of your Frostbolt, Ice Lance, Deep Freeze and Blizzard spells by $s1 yards and the radius of your Frost Nova and Cone of Cold spells by $s2%. |cFF9D9D9DAt max rank, your Frost damage is increased by up to 10% based on the target's distance, reaching full effect at 30 yards or more.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 131232, 'EffectSpellClassMaskA_2': 1048576, 'EffectSpellClassMaskB_1': 576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3},
)


arctic_reach_16758 = spell(
    id=16758,
    name='Arctic Reach',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=107, misc_value=5),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=6),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=154,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the range of your Frostbolt, Ice Lance, Deep Freeze and Blizzard spells by $s1 yards and the radius of your Frost Nova and Cone of Cold spells by $s2%.  Your Frost damage is increased by up to 10% based on the target's distance, reaching full effect at 30 yards or more.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 131232, 'EffectSpellClassMaskA_2': 1048576, 'EffectSpellClassMaskB_1': 576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3},
)


arcane_stability_16769 = spell(
    id=16769,
    name='Arcane Stability',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=79, implicit_target_a=1, apply_aura=108, misc_value=9),
    ],
    spell_icon_id=225,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the pushback suffered from damaging attacks while casting Arcane Missiles and Arcane Blast by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 536872960, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


arcane_stability_16770 = spell(
    id=16770,
    name='Arcane Stability',
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
    ],
    spell_icon_id=225,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the pushback suffered from damaging attacks while casting Arcane Missiles and Arcane Blast by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 536872960, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


incineration_18459 = spell(
    id=18459,
    name='Incineration',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1000, die_sides=0, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COOLDOWN),
        Effect(type=EffectType.APPLY_AURA, base_points=10, die_sides=0, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=678,
    notes='Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (0,0) rank 1: absorbs the old Improved Fire Blast. Both SpellMods scoped to Fire Blast alone (dword-0 bit 0x2). No crit modifier on purpose - Fire Blast always crits (sec 3.1).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Fire Blast by 1 sec and increases its damage by 10%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'EffectSpellClassMaskB_1': 2},
)


incineration_18460 = spell(
    id=18460,
    name='Incineration',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1500, die_sides=0, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COOLDOWN),
        Effect(type=EffectType.APPLY_AURA, base_points=20, die_sides=0, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=678,
    notes='Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (0,0) rank 2: absorbs the old Improved Fire Blast. Both SpellMods scoped to Fire Blast alone (dword-0 bit 0x2). No crit modifier on purpose - Fire Blast always crits (sec 3.1).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Fire Blast by 1.5 sec and increases its damage by 20%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'EffectSpellClassMaskB_1': 2},
)


frost_warding_28332 = spell(
    id=28332,
    name='Frost Warding',
    school=School.NORMAL,
    attributes=208,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=108, misc_value=8),
        Effect(type=EffectType.DUMMY, base_points=29),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=501,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the armor and resistances given by your Frost Armor and Ice Armor spells by $s1%.  In addition, gives your Frost Ward and Fire Ward a $s2% chance to negate the warded damage spell and restore mana equal to the damage caused.  While Frost Armor or Ice Armor is active, physical damage taken is reduced by an additional 20%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


winter_s_chill_28592 = spell(
    id=28592,
    name="Winter's Chill",
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=12579),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=187,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your chance to critically hit with Frostbolt by an additional $s2% and gives your Frost damage spells a $h% chance to apply the Winter's Chill effect, which increases the chance spells will critically hit the target by $12579s1% for $12579d.  Stacks up to $12579u times.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 66, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


winter_s_chill_28593 = spell(
    id=28593,
    name="Winter's Chill",
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=12579),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=187,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your chance to critically hit with Frostbolt by an additional $s2% and gives your Frost damage spells a $h% chance to apply the Winter's Chill effect, which increases the chance spells will critically hit the target by $12579s1% for $12579d.  Stacks up to $12579u times.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


master_of_elements_29074 = spell(
    id=29074,
    name='Master of Elements',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=1, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_PCT),
    ],
    spell_icon_id=1920,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (3,2) rank 1: EFFECT_0 DUMMY stays the refund percentage spell_mage_master_of_elements reads (0/0/40 - capstone on rank 3 only, stock was 10/20/30 at every rank); EFFECT_1 MOD_CRIT_PCT is the new 'all spells and abilities' crit.",
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your critical strike chance with all spells and abilities by 1%.\n\n|cFF9D9D9DCapstone Bonus: Your direct damage spell criticals refund 40% of their mana cost.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


master_of_elements_29075 = spell(
    id=29075,
    name='Master of Elements',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=2, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_PCT),
    ],
    spell_icon_id=1920,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (3,2) rank 2: EFFECT_0 DUMMY stays the refund percentage spell_mage_master_of_elements reads (0/0/40 - capstone on rank 3 only, stock was 10/20/30 at every rank); EFFECT_1 MOD_CRIT_PCT is the new 'all spells and abilities' crit.",
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your critical strike chance with all spells and abilities by 2%.\n\n|cFF9D9D9DCapstone Bonus: Your direct damage spell criticals refund 40% of their mana cost.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


master_of_elements_29076 = spell(
    id=29076,
    name='Master of Elements',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=40, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=3, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_PCT),
    ],
    spell_icon_id=1920,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (3,2) rank 3: EFFECT_0 DUMMY stays the refund percentage spell_mage_master_of_elements reads (0/0/40 - capstone on rank 3 only, stock was 10/20/30 at every rank); EFFECT_1 MOD_CRIT_PCT is the new 'all spells and abilities' crit.",
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your critical strike chance with all spells and abilities by 3%.\n\nCapstone Bonus: Your direct damage spell criticals refund 40% of their mana cost.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


precision_29438 = spell(
    id=29438,
    name='Precision',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=71, misc_value=16),
        Effect(type=EffectType.APPLY_AURA, base_points=-2, implicit_target_a=1, apply_aura=72, misc_value=126),
    ],
    spell_icon_id=172,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your critical strike chance with Frost spells by $s1% and reduces the mana cost of your spells by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_2': 1, 'EffectSpellClassMaskA_2': 69640, 'EffectSpellClassMaskB_2': 1, 'EffectSpellClassMaskC_2': 4096, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


precision_29439 = spell(
    id=29439,
    name='Precision',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=71, misc_value=16),
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=72, misc_value=126),
    ],
    spell_icon_id=172,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your critical strike chance with Frost spells by $s1% and reduces the mana cost of your spells by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_2': 1, 'EffectSpellClassMaskA_2': 69640, 'EffectSpellClassMaskC_2': 4096, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


precision_29440 = spell(
    id=29440,
    name='Precision',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=71, misc_value=16),
        Effect(type=EffectType.APPLY_AURA, base_points=-4, implicit_target_a=1, apply_aura=72, misc_value=126),
    ],
    spell_icon_id=172,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your critical strike chance with Frost spells by $s1% and reduces the mana cost of your spells by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_2': 1, 'EffectSpellClassMaskA_2': 69640, 'EffectSpellClassMaskC_2': 4096, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


magic_absorption_29441 = spell(
    id=29441,
    name='Magic Absorption',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=79, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=459,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 1): repoints stock Magic Absorption\'s slot (id 1650) to (1,0) - unrelated coordinate shuffle; the real Magic Absorption (resist-per-level + mana-on-full-resist) doesn\'t match this design\'s wording, so content is fully replaced. "Increases magic damage done by 1/2/3%. Reduces magic damage taken by 1/2/3%." effect1 SPELL_AURA_MOD_DAMAGE_PERCENT_DONE (79), effect2 SPELL_AURA_MOD_DAMAGE_PERCENT_TAKEN (87), both misc_value 126 (all magic schools). "Increases mana from Mana Gems by 15/30/45%" NOT built this phase - Mana Gems are items (SPELLFAMILY_GENERIC); a classmask-scoped SpellMod only matches within the caster\'s own spell family, so this needs a different mechanism - deferred to Phase 3. raw_overrides/effects fully replaced (not merged) - the earlier version left a stale points_per_level 0.5 and other fields from the real Magic Absorption data; caught and fixed.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases magic damage done by 1% and reduces magic damage taken by 1%. Increases the mana you gain from Mana Gems by 15%.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskA_3': 16},
)


magic_absorption_29444 = spell(
    id=29444,
    name='Magic Absorption',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=79, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=459,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 1): repoints stock Magic Absorption\'s slot (id 1650) to (1,0) - unrelated coordinate shuffle; the real Magic Absorption (resist-per-level + mana-on-full-resist) doesn\'t match this design\'s wording, so content is fully replaced. "Increases magic damage done by 1/2/3%. Reduces magic damage taken by 1/2/3%." effect1 SPELL_AURA_MOD_DAMAGE_PERCENT_DONE (79), effect2 SPELL_AURA_MOD_DAMAGE_PERCENT_TAKEN (87), both misc_value 126 (all magic schools). "Increases mana from Mana Gems by 15/30/45%" NOT built this phase - Mana Gems are items (SPELLFAMILY_GENERIC); a classmask-scoped SpellMod only matches within the caster\'s own spell family, so this needs a different mechanism - deferred to Phase 3. raw_overrides/effects fully replaced (not merged) - the earlier version left a stale points_per_level 0.5 and other fields from the real Magic Absorption data; caught and fixed.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases magic damage done by 2% and reduces magic damage taken by 2%. Increases the mana you gain from Mana Gems by 30%.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskA_3': 16},
)


improved_blink_31569 = spell(
    id=31569,
    name='Improved Blink',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=1, apply_aura=108, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=-2501, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=1499,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of Blink by $47000s1 sec and its mana cost by $s1%.\n\n|cFF9D9D9DCapstone Bonus: After casting Blink all damage taken is reduced by 20% for 3 sec.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 65536, 'EffectSpellClassMaskB_1': 65536, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


improved_blink_31570 = spell(
    id=31570,
    name='Improved Blink',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=108, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=-5001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1499,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of Blink by $47000s1 sec and its mana cost by $s1%.\n\nCapstone Bonus: After casting Blink all damage taken is reduced by 20% for 3 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 65536, 'EffectSpellClassMaskB_1': 65536, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


arcane_potency_31571 = spell(
    id=31571,
    name='Arcane Potency',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=12),
    ],
    spell_icon_id=2120,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your next damaging spell by $s1% after gaining Clearcasting or Presence of Mind.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 34, 'EffectSpellClassMaskB_1': 2099200, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


arcane_potency_31572 = spell(
    id=31572,
    name='Arcane Potency',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=12),
    ],
    spell_icon_id=2120,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your next damaging spell by $s1% after gaining Clearcasting or Presence of Mind.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 34, 'EffectSpellClassMaskB_1': 2099200, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


prismatic_cloak_31574 = spell(
    id=31574,
    name='Prismatic Cloak',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-2, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=-1501, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=2126,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces all damage taken by $s1% and reduces the fade time of your Invisibility spell by ${$m2/-1000} sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_2': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


prismatic_cloak_31575 = spell(
    id=31575,
    name='Prismatic Cloak',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=-3001, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=2126,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces all damage taken by $s1% and reduces the fade time of your Invisibility spell by ${$m2/-1000} sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_2': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


arcane_empowerment_31579 = spell(
    id=31579,
    name='Arcane Empowerment',
    school=School.NORMAL,
    attributes=80,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=108),
        Effect(type=65, implicit_target_a=1, apply_aura=79, misc_value=127, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=225,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases all damage by $s2%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Arcane Blast and Arcane Barrage spells by $s1% and the damage of your Arcane Missiles by $s3%. In addition, increases the damage of all party and raid members within 100 yds by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 536870912, 'EffectSpellClassMaskA_2': 32768, 'EffectSpellClassMaskC_1': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


arcane_empowerment_31582 = spell(
    id=31582,
    name='Arcane Empowerment',
    school=School.NORMAL,
    attributes=80,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108),
        Effect(type=65, base_points=1, implicit_target_a=1, apply_aura=79, misc_value=127, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=225,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases all damage by $s2%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Arcane Blast and Arcane Barrage spells by $s1% and the damage of your Arcane Missiles by $s3%. In addition, increases the damage of all party and raid members within 100 yds by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 536870912, 'EffectSpellClassMaskA_2': 32768, 'EffectSpellClassMaskC_1': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


arcane_empowerment_31583 = spell(
    id=31583,
    name='Arcane Empowerment',
    school=School.NORMAL,
    attributes=80,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108),
        Effect(type=65, base_points=2, implicit_target_a=1, apply_aura=79, misc_value=127, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=225,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases all damage by $s2%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Arcane Blast and Arcane Barrage spells by $s1% and the damage of your Arcane Missiles by $s3%. In addition, increases the damage of all party and raid members within 100 yds by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 536870912, 'EffectSpellClassMaskA_2': 32768, 'EffectSpellClassMaskC_1': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


mind_mastery_31584 = spell(
    id=31584,
    name='Mind Mastery',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=72, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=1999, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=2121,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell power by $s1% of your total Intellect.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 3, 'EffectSpellClassMaskA_1': 4043439104, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskC_3': 1},
)


mind_mastery_31585 = spell(
    id=31585,
    name='Mind Mastery',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=72, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=3999, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=2121,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell power by $s1% of your total Intellect.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 3, 'EffectSpellClassMaskA_1': 4043439104, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskC_3': 1},
)


mind_mastery_31586 = spell(
    id=31586,
    name='Mind Mastery',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-7, implicit_target_a=1, apply_aura=72, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=5999, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=2121,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell power by $s1% of your total Intellect.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 3, 'EffectSpellClassMaskA_1': 4043439104, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskC_3': 1},
)


mind_mastery_31587 = spell(
    id=31587,
    name='Mind Mastery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=174, misc_value=126),
    ],
    spell_icon_id=2121,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell power by $s1% of your total Intellect.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 3, 'EffectSpellClassMaskA_1': 4043439104, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


mind_mastery_31588 = spell(
    id=31588,
    name='Mind Mastery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=174, misc_value=126),
    ],
    spell_icon_id=2121,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell power by $s1% of your total Intellect.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 3, 'EffectSpellClassMaskA_1': 4043439104, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


playing_with_fire_31638 = spell(
    id=31638,
    name='Playing with Fire',
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
        Effect(type=EffectType.APPLY_AURA, base_points=1, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=1, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
    ],
    spell_icon_id=2130,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 3 (4,0): ProcTypeMask = PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS|_NEG (0x14000) - any direct spell-damage-class-magic hit done (periodic excluded at that flag level already; spell_mage_playing_with_fire also explicitly rejects PROC_FLAG_DONE_PERIODIC and Dragon's Breath itself). CD reduction is a flat 1 sec (2 sec on crit) at every rank - this clause doesn't scale with rank, only the damage-mod percentages do.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases all damage done by 1% and all magic damage taken by 1%.\n\nEach spell you cast that deals direct magic damage reduces the cooldown of your Dragon's Breath by 1 sec, doubled when dealing a critical strike. Dragon's Breath cannot reduce its own cooldown.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'ProcTypeMask': 81920},
)


playing_with_fire_31639 = spell(
    id=31639,
    name='Playing with Fire',
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
        Effect(type=EffectType.APPLY_AURA, base_points=2, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=2, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
    ],
    spell_icon_id=2130,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 3 (4,0): ProcTypeMask = PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS|_NEG (0x14000) - any direct spell-damage-class-magic hit done (periodic excluded at that flag level already; spell_mage_playing_with_fire also explicitly rejects PROC_FLAG_DONE_PERIODIC and Dragon's Breath itself). CD reduction is a flat 1 sec (2 sec on crit) at every rank - this clause doesn't scale with rank, only the damage-mod percentages do.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases all damage done by 2% and all magic damage taken by 2%.\n\nEach spell you cast that deals direct magic damage reduces the cooldown of your Dragon's Breath by 1 sec, doubled when dealing a critical strike. Dragon's Breath cannot reduce its own cooldown.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'ProcTypeMask': 81920},
)


playing_with_fire_31640 = spell(
    id=31640,
    name='Playing with Fire',
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
        Effect(type=EffectType.APPLY_AURA, base_points=3, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=3, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
    ],
    spell_icon_id=2130,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 3 (4,0): ProcTypeMask = PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS|_NEG (0x14000) - any direct spell-damage-class-magic hit done (periodic excluded at that flag level already; spell_mage_playing_with_fire also explicitly rejects PROC_FLAG_DONE_PERIODIC and Dragon's Breath itself). CD reduction is a flat 1 sec (2 sec on crit) at every rank - this clause doesn't scale with rank, only the damage-mod percentages do.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases all damage done by 3% and all magic damage taken by 3%.\n\nEach spell you cast that deals direct magic damage reduces the cooldown of your Dragon's Breath by 1 sec, doubled when dealing a critical strike. Dragon's Breath cannot reduce its own cooldown.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'ProcTypeMask': 81920},
)


blazing_speed_31641 = spell(
    id=31641,
    name='Blazing Speed',
    school=School.FIRE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MOD_CASTING_SPEED_NOT_STACK),
        Effect(type=EffectType.APPLY_AURA, base_points=1, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MOD_LEECH_PCT),
    ],
    spell_icon_id=2127,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (7,0) rank 1: moved from (5,0), now 3 ranks. Pure data: passive spell haste (aura 65) + leech (aura 295, this fork's SPELL_AURA_MOD_LEECH_PCT - Unit::DealDamage heals the caster for the % of direct+periodic damage, can't crit, ignores healing-received mods). The stock proc-trigger escape (18350) is gone; the health-gated capstone is rank 3 only (200107), Phase 3.",
    raw_overrides={'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell haste by 1% and causes your damage to heal you for 1% of the damage dealt.\n\n|cFF9D9D9DCapstone Bonus: Taking direct damage while below 35% health dispels all movement impairing effects and increases your movement speed by 50% and your haste by 20% for 6 sec. While active, you can cast non-channeled Fire spells while moving. This effect can only occur every 30 sec.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


blazing_speed_31642 = spell(
    id=31642,
    name='Blazing Speed',
    school=School.FIRE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MOD_CASTING_SPEED_NOT_STACK),
        Effect(type=EffectType.APPLY_AURA, base_points=2, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MOD_LEECH_PCT),
    ],
    spell_icon_id=2127,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (7,0) rank 2: moved from (5,0), now 3 ranks. Pure data: passive spell haste (aura 65) + leech (aura 295, this fork's SPELL_AURA_MOD_LEECH_PCT - Unit::DealDamage heals the caster for the % of direct+periodic damage, can't crit, ignores healing-received mods). The stock proc-trigger escape (18350) is gone; the health-gated capstone is rank 3 only (200107), Phase 3.",
    raw_overrides={'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell haste by 2% and causes your damage to heal you for 2% of the damage dealt.\n\n|cFF9D9D9DCapstone Bonus: Taking direct damage while below 35% health dispels all movement impairing effects and increases your movement speed by 50% and your haste by 20% for 6 sec. While active, you can cast non-channeled Fire spells while moving. This effect can only occur every 30 sec.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


empowered_fire_31656 = spell(
    id=31656,
    name='Empowered Fire',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.BONUS_MULTIPLIER),
        Effect(type=EffectType.APPLY_AURA, base_points=33, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=185,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (7,2) rank 1: scaling 7% (was 5/10/15), scoped to Fireball + Pyroblast (dword 0) and Living Bomb (dword 1, replacing stock's Frostfire Bolt). EFFECT_1 DUMMY = mana-return chance marker (33) for the Phase 3 rework of spell_mage_empowered_fire (1% base mana, was 2%). NOTE: the rank-3 'Living Bomb periodic can crit' capstone is a no-op on this fork - AuraEffect::CalcPeriodicCritChance lets every DoT crit unconditionally already; flagged in the playtest doc.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the spell damage scaling of your Fireball, Pyroblast and Living Bomb spells by 7%. Each time your Ignite talent causes damage, you have a 33% chance to regain 1% of your base mana.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194305, 'EffectSpellClassMaskA_2': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 33, 'ProcTypeMask': 262144, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


empowered_fire_31657 = spell(
    id=31657,
    name='Empowered Fire',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=13, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.BONUS_MULTIPLIER),
        Effect(type=EffectType.APPLY_AURA, base_points=66, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=185,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (7,2) rank 2: scaling 14% (was 5/10/15), scoped to Fireball + Pyroblast (dword 0) and Living Bomb (dword 1, replacing stock's Frostfire Bolt). EFFECT_1 DUMMY = mana-return chance marker (66) for the Phase 3 rework of spell_mage_empowered_fire (1% base mana, was 2%). NOTE: the rank-3 'Living Bomb periodic can crit' capstone is a no-op on this fork - AuraEffect::CalcPeriodicCritChance lets every DoT crit unconditionally already; flagged in the playtest doc.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the spell damage scaling of your Fireball, Pyroblast and Living Bomb spells by 14%. Each time your Ignite talent causes damage, you have a 66% chance to regain 1% of your base mana.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194305, 'EffectSpellClassMaskA_2': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 67, 'ProcTypeMask': 262144, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


empowered_fire_31658 = spell(
    id=31658,
    name='Empowered Fire',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.BONUS_MULTIPLIER),
        Effect(type=EffectType.APPLY_AURA, base_points=100, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=185,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (7,2) rank 3: scaling 20% (was 5/10/15), scoped to Fireball + Pyroblast (dword 0) and Living Bomb (dword 1, replacing stock's Frostfire Bolt). EFFECT_1 DUMMY = mana-return chance marker (100) for the Phase 3 rework of spell_mage_empowered_fire (1% base mana, was 2%). NOTE: the rank-3 'Living Bomb periodic can crit' capstone is a no-op on this fork - AuraEffect::CalcPeriodicCritChance lets every DoT crit unconditionally already; flagged in the playtest doc.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the spell damage scaling of your Fireball, Pyroblast and Living Bomb spells by 20%. Each time your Ignite talent causes damage, you have a 100% chance to regain 1% of your base mana.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194305, 'EffectSpellClassMaskA_2': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 262144, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


frozen_core_31667 = spell(
    id=31667,
    name='Frozen Core',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200016),
    ],
    spell_icon_id=2132,
    notes='Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 5, Frozen Core). effect1 (magic dmg taken -2/4/6%) needed zero changes -- pulled data already matched spec exactly. effect2 (new, all 3 ranks): native SPELL_AURA_PROC_TRIGGER_SPELL, \'taking magic damage grants Frozen Core, +2/4/6% Frost damage for 8 sec\' -- pure data, one small dedicated buff spell per rank (200016/17/18) since the % scales by rank and each rank only ever triggers its own. ProcTypeMask = PROC_FLAG_TAKEN_SPELL_MAGIC_DMG_CLASS_NEG | PROC_FLAG_TAKEN_PERIODIC (131072|524288) so it reacts to any class\'s direct or DoT magic damage, not just Mage-family sources. Playtest bugfix (2026-08-27/28, user call, "Frozen Core does nothing at all"): this spell has no explicit spell_proc row, so SpellMgr::LoadSpellProcs\'s fallback generator builds one from the DBC data itself -- and that generator ORs together the SpellClassMask of *every* trigger-aura effect on the entry (not just the proc-relevant ones) into a single spell-wide SpellFamilyMask, via SPELL_AURA_MOD_DAMAGE_PERCENT_TAKEN (effect1\'s aura type) itself being in SpellMgr\'s isTriggerAura[] table. Effect1\'s EffectSpellClassMaskA_1/B_1 (160/576) were leftover cruft from the pre-rework spell this ID used to be (\\"pulled from existing data\\" above) -- harmless for effect1 itself (a plain percent-taken modifier, not proc-scoped), but they got sucked into the generated procEntry\'s SpellFamilyMask and silently required every trigger spell family-mask-affect *that specific leftover mask*, which nothing (not a mob\'s fireball, not even the mage\'s own Ice Lance) ever matches. Confirmed live via temporary LOG_ERROR tracing in Aura::GetProcEffectMask/CanSpellTriggerProcOnEvent (SpellAuras.cpp/SpellMgr.cpp) -- procEntry.SpellFamilyName resolved to 3 (Mage) and SpellFamilyMask to the leftover value, failing IsAffected() for every real event. Removed EffectSpellClassMaskA_1/B_1 entirely (all 3 ranks) so the fallback procEntry\'s SpellFamilyMask stays 0/unrestricted, matching the documented intent.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces the damage taken from all spells by $s1%. |cFF9D9D9DAt max rank, your Ice Lance critical strikes against frozen targets pierce to the target's core, dealing Frost damage over 8 sec. Does not stack, and refreshes on reapplication.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'RangeIndex': 1, 'SpellClassSet': 3, 'ProcTypeMask': 655360},
)


frozen_core_31668 = spell(
    id=31668,
    name='Frozen Core',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200017),
    ],
    spell_icon_id=2132,
    notes='Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 5, Frozen Core). effect1 (magic dmg taken -2/4/6%) needed zero changes -- pulled data already matched spec exactly. effect2 (new, all 3 ranks): native SPELL_AURA_PROC_TRIGGER_SPELL, \'taking magic damage grants Frozen Core, +2/4/6% Frost damage for 8 sec\' -- pure data, one small dedicated buff spell per rank (200016/17/18) since the % scales by rank and each rank only ever triggers its own. ProcTypeMask = PROC_FLAG_TAKEN_SPELL_MAGIC_DMG_CLASS_NEG | PROC_FLAG_TAKEN_PERIODIC (131072|524288) so it reacts to any class\'s direct or DoT magic damage, not just Mage-family sources. Playtest bugfix (2026-08-27/28, user call, "Frozen Core does nothing at all"): this spell has no explicit spell_proc row, so SpellMgr::LoadSpellProcs\'s fallback generator builds one from the DBC data itself -- and that generator ORs together the SpellClassMask of *every* trigger-aura effect on the entry (not just the proc-relevant ones) into a single spell-wide SpellFamilyMask, via SPELL_AURA_MOD_DAMAGE_PERCENT_TAKEN (effect1\'s aura type) itself being in SpellMgr\'s isTriggerAura[] table. Effect1\'s EffectSpellClassMaskA_1/B_1 (160/576) were leftover cruft from the pre-rework spell this ID used to be (\\"pulled from existing data\\" above) -- harmless for effect1 itself (a plain percent-taken modifier, not proc-scoped), but they got sucked into the generated procEntry\'s SpellFamilyMask and silently required every trigger spell family-mask-affect *that specific leftover mask*, which nothing (not a mob\'s fireball, not even the mage\'s own Ice Lance) ever matches. Confirmed live via temporary LOG_ERROR tracing in Aura::GetProcEffectMask/CanSpellTriggerProcOnEvent (SpellAuras.cpp/SpellMgr.cpp) -- procEntry.SpellFamilyName resolved to 3 (Mage) and SpellFamilyMask to the leftover value, failing IsAffected() for every real event. Removed EffectSpellClassMaskA_1/B_1 entirely (all 3 ranks) so the fallback procEntry\'s SpellFamilyMask stays 0/unrestricted, matching the documented intent.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces the damage taken from all spells by $s1%. |cFF9D9D9DAt max rank, your Ice Lance critical strikes against frozen targets pierce to the target's core, dealing Frost damage over 8 sec. Does not stack, and refreshes on reapplication.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'RangeIndex': 1, 'SpellClassSet': 3, 'ProcTypeMask': 655360},
)


frozen_core_31669 = spell(
    id=31669,
    name='Frozen Core',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-7, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200018),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200019),
    ],
    spell_icon_id=2132,
    notes='Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 5, Frozen Core). effect1 (magic dmg taken -2/4/6%) needed zero changes -- pulled data already matched spec exactly. effect2 (new, all 3 ranks): native SPELL_AURA_PROC_TRIGGER_SPELL, \'taking magic damage grants Frozen Core, +2/4/6% Frost damage for 8 sec\' -- pure data, one small dedicated buff spell per rank (200016/17/18) since the % scales by rank and each rank only ever triggers its own. ProcTypeMask = PROC_FLAG_TAKEN_SPELL_MAGIC_DMG_CLASS_NEG | PROC_FLAG_TAKEN_PERIODIC (131072|524288) so it reacts to any class\'s direct or DoT magic damage, not just Mage-family sources. Playtest bugfix (2026-08-27/28, user call, "Frozen Core does nothing at all"): this spell has no explicit spell_proc row, so SpellMgr::LoadSpellProcs\'s fallback generator builds one from the DBC data itself -- and that generator ORs together the SpellClassMask of *every* trigger-aura effect on the entry (not just the proc-relevant ones) into a single spell-wide SpellFamilyMask, via SPELL_AURA_MOD_DAMAGE_PERCENT_TAKEN (effect1\'s aura type) itself being in SpellMgr\'s isTriggerAura[] table. Effect1\'s EffectSpellClassMaskA_1/B_1 (160/576) were leftover cruft from the pre-rework spell this ID used to be (\\"pulled from existing data\\" above) -- harmless for effect1 itself (a plain percent-taken modifier, not proc-scoped), but they got sucked into the generated procEntry\'s SpellFamilyMask and silently required every trigger spell family-mask-affect *that specific leftover mask*, which nothing (not a mob\'s fireball, not even the mage\'s own Ice Lance) ever matches. Confirmed live via temporary LOG_ERROR tracing in Aura::GetProcEffectMask/CanSpellTriggerProcOnEvent (SpellAuras.cpp/SpellMgr.cpp) -- procEntry.SpellFamilyName resolved to 3 (Mage) and SpellFamilyMask to the leftover value, failing IsAffected() for every real event. Removed EffectSpellClassMaskA_1/B_1 entirely (all 3 ranks) so the fallback procEntry\'s SpellFamilyMask stays 0/unrestricted, matching the documented intent. effect3 (rank 3 only, capstone): \'Ice Lance crit vs frozen -> DoT (200019), no stack, refresh on reapply.\' Native aura reapplication already gives \'does not stack, refreshes\' for free (same-spell-ID single-target apply). Real gating (Ice Lance only + must crit + target frozen) lives entirely in spell_mage_frozen_core (spell_mage.cpp), not in the DBC row: effect2 and effect3 share this spell\'s one spell-wide ProcFlags/SchoolMask/SpellFamilyMask (confirmed by reading Aura::GetProcEffectMask/CanSpellTriggerProcOnEvent), so a script has to discriminate \'taken\' (effect2) from \'done+crit+frozen\' (effect3) per event rather than two independently-scoped native effects.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces the damage taken from all spells by $s1%.  Your Ice Lance critical strikes against frozen targets pierce to the target's core, dealing Frost damage over 8 sec. Does not stack, and refreshes on reapplication.", 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'RangeIndex': 1, 'SpellClassSet': 3, 'ProcTypeMask': 720896},
)


ice_floes_31670 = spell(
    id=31670,
    name='Ice Floes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-12, implicit_target_a=1, apply_aura=108, misc_value=11),
    ],
    spell_icon_id=2133,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Frost Nova, Cone of Cold, Ice Block and Icy Veins spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 576, 'EffectSpellClassMaskA_2': 16512, 'EffectSpellClassMaskB_1': 576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3},
)


ice_floes_31672 = spell(
    id=31672,
    name='Ice Floes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-23, implicit_target_a=1, apply_aura=108, misc_value=11),
    ],
    spell_icon_id=2133,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Frost Nova, Cone of Cold, Ice Block and Icy Veins spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 576, 'EffectSpellClassMaskA_2': 16512, 'EffectSpellClassMaskB_1': 576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3},
)


arctic_winds_31674 = spell(
    id=31674,
    name='Arctic Winds',
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
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=79, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=79, misc_value=16),
    ],
    spell_icon_id=2131,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all damage you deal by $s1% and Frost damage you deal by $s3%. |cFF9D9D9DAt max rank, your Glacial Spike shatters on impact, striking up to 5 additional enemies within 8 yards.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3},
)


arctic_winds_31675 = spell(
    id=31675,
    name='Arctic Winds',
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
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=79, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=79, misc_value=16),
    ],
    spell_icon_id=2131,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all damage you deal by $s1% and Frost damage you deal by $s3%. |cFF9D9D9DAt max rank, your Glacial Spike shatters on impact, striking up to 5 additional enemies within 8 yards.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3},
)


arctic_winds_31676 = spell(
    id=31676,
    name='Arctic Winds',
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
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=79, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=79, misc_value=16),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2131,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all damage you deal by $s1% and Frost damage you deal by $s3%.  Your Glacial Spike shatters on impact, striking up to 5 additional enemies within 8 yards.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3},
)


molten_fury_31679 = spell(
    id=31679,
    name='Molten Fury',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=112, misc_value=4919),
    ],
    spell_icon_id=2129,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases damage of all spells against targets with less than 35% health by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 551686903, 'EffectSpellClassMaskA_2': 102472, 'EffectSpellClassMaskB_1': 576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3},
)


molten_fury_31680 = spell(
    id=31680,
    name='Molten Fury',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=112, misc_value=4920),
    ],
    spell_icon_id=2129,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases damage of all spells against targets with less than 35% health by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 551686903, 'EffectSpellClassMaskA_2': 102472, 'EffectSpellClassMaskB_1': 576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3},
)


empowered_frostbolt_31682 = spell(
    id=31682,
    name='Empowered Frostbolt',
    school=School.FROST,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200023),
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=107, misc_value=10),
    ],
    spell_icon_id=188,
    notes='Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 8, Empowering Frostbolt). effect2 (cast time -0.1/0.2 sec, SPELLMOD_CASTING_TIME) needed zero changes -- matched spec exactly already. effect1 was the OLD \'Empowered Frostbolt\' mechanic (a direct SPELLMOD_BONUS_MULTIPLIER damage bonus on Frostbolt itself) -- a different shape than the new spec\'s post-cast buff, replaced outright: native PROC_TRIGGER_SPELL (100%, on casting Frostbolt) to a new buff (200023/200024): crit-damage-bonus +7/14% (ADD_PCT_MODIFIER, SPELLMOD_CRIT_DAMAGE_BONUS, empty classmask = \'of your spells\' broadly, same convention as Winter\'s Chill\'s own crit% effect) + Frost damage +3/5% (MOD_DAMAGE_PERCENT_DONE, Frost school mask), 8 sec, pure data. Playtest bugfix (2026-08-27, second recurrence found via an automated sweep of every spell/talent CSV, built through lib/build.py and checked for a SPELLMOD-type effect whose own classmask came out all-zero): the SPELLMOD_CASTING_TIME modifier lives on effect index 1 (the second effect, letter B), but its Frostbolt-only classmask (32) was stored under EffectSpellClassMaskA_1 - effect index 0 (letter A, the PROC_TRIGGER_SPELL effect, which doesn\'t need one at all) - leaving effect 1\'s real classmask all-zero, i.e. "matches every mage spell," same root cause as Permafrost/Chilled to the Bone (frost_mage_rework.sql (merged Frost Mage rework migration; originally rev_1787820084006262155.sql) / docs/dbc-build-pipeline.md "Bug 3"). Moved to EffectSpellClassMaskB_1, which is what the engine actually reads for effect index 1.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Frostbolt spell by an amount equal to $s1% of your spell power and reduces the cast time by ${$m2/-1000}.1 sec.', 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'ProcTypeMask': 65536, 'EffectSpellClassMaskB_1': 32},
)


empowered_frostbolt_31683 = spell(
    id=31683,
    name='Empowered Frostbolt',
    school=School.FROST,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200024),
        Effect(type=EffectType.APPLY_AURA, base_points=-201, implicit_target_a=1, apply_aura=107, misc_value=10),
    ],
    spell_icon_id=188,
    notes='Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 8, Empowering Frostbolt). effect2 (cast time -0.1/0.2 sec, SPELLMOD_CASTING_TIME) needed zero changes -- matched spec exactly already. effect1 was the OLD \'Empowered Frostbolt\' mechanic (a direct SPELLMOD_BONUS_MULTIPLIER damage bonus on Frostbolt itself) -- a different shape than the new spec\'s post-cast buff, replaced outright: native PROC_TRIGGER_SPELL (100%, on casting Frostbolt) to a new buff (200023/200024): crit-damage-bonus +7/14% (ADD_PCT_MODIFIER, SPELLMOD_CRIT_DAMAGE_BONUS, empty classmask = \'of your spells\' broadly, same convention as Winter\'s Chill\'s own crit% effect) + Frost damage +3/5% (MOD_DAMAGE_PERCENT_DONE, Frost school mask), 8 sec, pure data. Playtest bugfix (2026-08-27, second recurrence found via an automated sweep of every spell/talent CSV, built through lib/build.py and checked for a SPELLMOD-type effect whose own classmask came out all-zero): the SPELLMOD_CASTING_TIME modifier lives on effect index 1 (the second effect, letter B), but its Frostbolt-only classmask (32) was stored under EffectSpellClassMaskA_1 - effect index 0 (letter A, the PROC_TRIGGER_SPELL effect, which doesn\'t need one at all) - leaving effect 1\'s real classmask all-zero, i.e. "matches every mage spell," same root cause as Permafrost/Chilled to the Bone (frost_mage_rework.sql (merged Frost Mage rework migration; originally rev_1787820084006262155.sql) / docs/dbc-build-pipeline.md "Bug 3"). Moved to EffectSpellClassMaskB_1, which is what the engine actually reads for effect index 1.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Frostbolt spell by an amount equal to $s1% of your spell power and reduces the cast time by ${$m2/-1000}.1 sec.', 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'ProcTypeMask': 65536, 'EffectSpellClassMaskB_1': 32},
)


pyromaniac_34293 = spell(
    id=34293,
    name='Pyromaniac',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_SPELL_CRIT_CHANCE_SCHOOL, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=25, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2128,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (9,1) rank 1: mana regen clause removed; EFFECT_1 DUMMY = extra Ignite contribution for Fireball crits (25%, x1.25 bank), read by Phase 3's spell_mage_ignite by icon 2128.",
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your critical strike chance by 2%. Your Fireball critical strikes contribute an additional 25% to your Ignite.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 12582935, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


pyromaniac_34295 = spell(
    id=34295,
    name='Pyromaniac',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.MOD_SPELL_CRIT_CHANCE_SCHOOL, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=50, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2128,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (9,1) rank 2: mana regen clause removed; EFFECT_1 DUMMY = extra Ignite contribution for Fireball crits (50%, x1.50 bank), read by Phase 3's spell_mage_ignite by icon 2128.",
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your critical strike chance by 4%. Your Fireball critical strikes contribute an additional 50% to your Ignite.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 12582935, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


pyromaniac_34296 = spell(
    id=34296,
    name='Pyromaniac',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.MOD_SPELL_CRIT_CHANCE_SCHOOL, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=75, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2128,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (9,1) rank 3: mana regen clause removed; EFFECT_1 DUMMY = extra Ignite contribution for Fireball crits (75%, x1.75 bank), read by Phase 3's spell_mage_ignite by icon 2128.",
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your critical strike chance by 6%. Your Fireball critical strikes contribute an additional 75% to your Ignite.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 12582935, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
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
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=57),
    ],
    spell_icon_id=2130,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your critical strike chance with spells by an additional $s2% and gives you a $h% chance when hit by a physical attack to reduce the cast time of your next Shadow Bolt or Incinerate spell by $34936s1%.  This effect lasts $34936d and will not occur more than once every 8 seconds.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194325, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 8, 'ProcTypeMask': 680, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
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
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=57),
    ],
    spell_icon_id=2130,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your critical strike chance with spells by an additional $s2% and gives you a $h% chance when hit by a physical attack to reduce the cast time of your next Shadow Bolt or Incinerate spell by $34936s1%.  This effect lasts $34936d and will not occur more than once every 8 seconds.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194325, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 16, 'ProcTypeMask': 680, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
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
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=57),
    ],
    spell_icon_id=2130,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your critical strike chance with spells by an additional $s2% and gives you a $h% chance when hit by a physical attack to reduce the cast time of your next Shadow Bolt or Incinerate spell by $34936s1%.  This effect lasts $34936d and will not occur more than once every 8 seconds.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194325, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 25, 'ProcTypeMask': 680, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


spell_power_35578 = spell(
    id=35578,
    name='Spell Power',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=2281,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases critical strike damage bonus of all spells by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Dealing direct critical damage with a spell while your mana is below 50% taps into raw power, restoring 1% of your total mana each second and increasing your magic damage by 10% and Arcane damage by another 5%. This effect lasts for 10 seconds and can only occur once every 30 seconds.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 551686903, 'EffectSpellClassMaskA_2': 102472, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


spell_power_35581 = spell(
    id=35581,
    name='Spell Power',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=74, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=2281,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases critical strike damage bonus of all spells by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Dealing direct critical damage with a spell while your mana is below 50% taps into raw power, restoring 1% of your total mana each second and increasing your magic damage by 10% and Arcane damage by another 5%. This effect lasts for 10 seconds and can only occur once every 30 seconds.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 551686903, 'EffectSpellClassMaskA_2': 102472, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


arcane_flows_44378 = spell(
    id=44378,
    name='Arcane Flows',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-16, implicit_target_a=1, apply_aura=108, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=-15001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=2940,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Presence of Mind, Arcane Power and Invisibility spells by $s1% and the cooldown of your Evocation spell by $/1000;s2 sec.\n\n|cFF9D9D9DCapstone Bonus: Your Arcane Power increases your magic damage dealt by an additional 5%.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 4, 'EffectSpellClassMaskA_2': 786464, 'EffectSpellClassMaskB_1': 67108864, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'EffectSpellClassMaskA_3': 2},
)


arcane_flows_44379 = spell(
    id=44379,
    name='Arcane Flows',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-30001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2940,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Presence of Mind, Arcane Power and Invisibility spells by $s1% and the cooldown of your Evocation spell by $/1000;s2 sec.\n\nCapstone Bonus: Your Arcane Power increases your magic damage dealt by an additional 5%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 4, 'EffectSpellClassMaskA_2': 786464, 'EffectSpellClassMaskB_1': 67108864, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'EffectSpellClassMaskA_3': 2},
)


netherwind_presence_44400 = spell(
    id=44400,
    name='Netherwind Presence',
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
    ],
    spell_icon_id=2943,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell haste by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Casting Slow while Netherwind Presence is fully stacked increases your movement speed by 50% for 5 sec. This effect cannot occur more than once every 30 sec.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'RangeIndex': 1, 'SpellClassSet': 3, 'ProcTypeMask': 65536, 'ProcCharges': 0},
)


netherwind_presence_44402 = spell(
    id=44402,
    name='Netherwind Presence',
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
    ],
    spell_icon_id=2943,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell haste by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Casting Slow while Netherwind Presence is fully stacked increases your movement speed by 50% for 5 sec. This effect cannot occur more than once every 30 sec.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'RangeIndex': 1, 'SpellClassSet': 3, 'ProcTypeMask': 65536, 'ProcCharges': 0},
)


netherwind_presence_44403 = spell(
    id=44403,
    name='Netherwind Presence',
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
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2943,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell haste by $s1%.\n\nCapstone Bonus: Casting Slow while Netherwind Presence is fully stacked increases your movement speed by 50% for 5 sec. This effect cannot occur more than once every 30 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'RangeIndex': 1, 'SpellClassSet': 3, 'ProcTypeMask': 65536, 'ProcCharges': 0},
)


missile_barrage_44404 = spell(
    id=44404,
    name='Missile Barrage',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=44401),
    ],
    spell_icon_id=3261,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your Arcane Blast a $h% chance, and your Arcane Barrage, Fireball, Frostbolt and Frostfire Bolt spells a ${$h/2}% chance to reduce the channeled duration of the next Arcane Missiles spell by $44401s1%, reduce the mana cost by $44401s3%, and missiles will fire every .5 secs.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 12, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3},
)


firestarter_44442 = spell(
    id=44442,
    name='Firestarter',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1000, die_sides=0, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.DURATION),
    ],
    spell_icon_id=3262,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (8,0) rank 1: duration only - the instant-Flamestrike proc is now rank 2's capstone.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the duration of your Dragon's Breath by 1 sec.\n\n|cFF9D9D9DCapstone Bonus: Your damaging Blast Wave, Dragon's Breath and Meteor spells make your next Flamestrike spell instant cast, cost no mana, and deal 30% more direct damage.|r", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8388608, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


firestarter_44443 = spell(
    id=44443,
    name='Firestarter',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2000, die_sides=0, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.DURATION),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=54741),
    ],
    spell_icon_id=3262,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (8,0) rank 2: EFFECT_1 is the capstone proc - 100% on damaging Blast Wave (dword 1 bit 0x40) / Dragon's Breath (dword 0 bit 0x800000) / Meteor (custom dword 2 bit 0x20), triggering the stock Firestarter buff 54741 (now also +30% Flamestrike direct damage).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the duration of your Dragon's Breath by 2 sec.\n\nCapstone Bonus: Your damaging Blast Wave, Dragon's Breath and Meteor spells make your next Flamestrike spell instant cast, cost no mana, and deal 30% more direct damage.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8388608, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskB_1': 8388608, 'EffectSpellClassMaskB_2': 64, 'EffectSpellClassMaskB_3': 32},
)


hot_streak_44445 = spell(
    id=44445,
    name='Hot Streak',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=33, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2999,
    notes='Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (8,2) rank 1: EFFECT_0 DUMMY is now the Mastery-scaling percentage (33) rather than the proc chance - the proc itself is unconditional (Phase 3 rewrites spell_mage_hot_streak; the trigger list lives in spell_proc -44445, which already excludes Pyroblast). Stock EFFECT_1 dropped.',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Any time you score 2 non-periodic spell criticals in a row using Fireball, Fire Blast, Scorch, Living Bomb, or Frostfire Bolt, your next Pyroblast spell cast within 10 sec will be instant cast. This Pyroblast always critically strikes and deals increased damage equal to 33% of your Mastery.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 8, 'EffectSpellClassMaskC_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


hot_streak_44446 = spell(
    id=44446,
    name='Hot Streak',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=66, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2999,
    notes='Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (8,2) rank 2: EFFECT_0 DUMMY is now the Mastery-scaling percentage (66) rather than the proc chance - the proc itself is unconditional (Phase 3 rewrites spell_mage_hot_streak; the trigger list lives in spell_proc -44445, which already excludes Pyroblast). Stock EFFECT_1 dropped.',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Any time you score 2 non-periodic spell criticals in a row using Fireball, Fire Blast, Scorch, Living Bomb, or Frostfire Bolt, your next Pyroblast spell cast within 10 sec will be instant cast. This Pyroblast always critically strikes and deals increased damage equal to 66% of your Mastery.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 8, 'EffectSpellClassMaskC_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


hot_streak_44448 = spell(
    id=44448,
    name='Hot Streak',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=100, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2999,
    notes='Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (8,2) rank 3: EFFECT_0 DUMMY is now the Mastery-scaling percentage (100) rather than the proc chance - the proc itself is unconditional (Phase 3 rewrites spell_mage_hot_streak; the trigger list lives in spell_proc -44445, which already excludes Pyroblast). Stock EFFECT_1 dropped.',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Any time you score 2 non-periodic spell criticals in a row using Fireball, Fire Blast, Scorch, Living Bomb, or Frostfire Bolt, your next Pyroblast spell cast within 10 sec will be instant cast. This Pyroblast always critically strikes and deals increased damage equal to 100% of your Mastery.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 8, 'EffectSpellClassMaskC_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


burnout_44449 = spell(
    id=44449,
    name='Burnout',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.CRIT_DAMAGE_BONUS),
        Effect(type=EffectType.APPLY_AURA, base_points=0, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2998,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (6,0) rank 1: 3 ranks (was 5). SPELLMOD_CRIT_DAMAGE_BONUS +40% on the crit bonus half: 1.5 -> 1.70x. EFFECT_1 DUMMY is the capstone marker (1 on rank 3 only) for Phase 3's Burnout scripts. Ranks 4-5 (44471/44472) are no longer granted.",
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spell critical strikes now deal 170% damage.\n\n|cFF9D9D9DCapstone Bonus: Dealing direct Fire damage to targets afflicted by your Ignite increases your spell damage by 6% for 8 sec. Dealing direct magic non-Fire damage to targets affected by your Ignite causes an explosion, dealing damage to all nearby enemies. Both effects require the final rank of Ignite.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 551686903, 'EffectSpellClassMaskA_2': 233544, 'EffectSpellClassMaskC_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'ProcTypeMask': 81920, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


burnout_44469 = spell(
    id=44469,
    name='Burnout',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=69, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.CRIT_DAMAGE_BONUS),
        Effect(type=EffectType.APPLY_AURA, base_points=0, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2998,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (6,0) rank 2: 3 ranks (was 5). SPELLMOD_CRIT_DAMAGE_BONUS +70% on the crit bonus half: 1.5 -> 1.85x. EFFECT_1 DUMMY is the capstone marker (1 on rank 3 only) for Phase 3's Burnout scripts. Ranks 4-5 (44471/44472) are no longer granted.",
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spell critical strikes now deal 185% damage.\n\n|cFF9D9D9DCapstone Bonus: Dealing direct Fire damage to targets afflicted by your Ignite increases your spell damage by 6% for 8 sec. Dealing direct magic non-Fire damage to targets affected by your Ignite causes an explosion, dealing damage to all nearby enemies. Both effects require the final rank of Ignite.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 551686903, 'EffectSpellClassMaskA_2': 233544, 'EffectSpellClassMaskC_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'ProcTypeMask': 81920, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


burnout_44470 = spell(
    id=44470,
    name='Burnout',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.CRIT_DAMAGE_BONUS),
        Effect(type=EffectType.APPLY_AURA, base_points=1, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2998,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (6,0) rank 3: 3 ranks (was 5). SPELLMOD_CRIT_DAMAGE_BONUS +100% on the crit bonus half: 1.5 -> 2.00x. EFFECT_1 DUMMY is the capstone marker (1 on rank 3 only) for Phase 3's Burnout scripts. Ranks 4-5 (44471/44472) are no longer granted.",
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spell critical strikes now deal 200% damage.\n\nCapstone Bonus: Dealing direct Fire damage to targets afflicted by your Ignite increases your spell damage by 6% for 8 sec. Dealing direct magic non-Fire damage to targets affected by your Ignite causes an explosion, dealing damage to all nearby enemies. Both effects require the final rank of Ignite.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 551686903, 'EffectSpellClassMaskA_2': 233544, 'EffectSpellClassMaskC_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'ProcTypeMask': 81920, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


burnout_44471 = spell(
    id=44471,
    name='Burnout',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=108, misc_value=15),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2998,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your spell critical damage bonus with all spells by $s1% but your non-periodic spell criticals cost an additional $s2% of the spell's cost.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 551686903, 'EffectSpellClassMaskA_2': 233544, 'EffectSpellClassMaskC_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 327680, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


burnout_44472 = spell(
    id=44472,
    name='Burnout',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=108, misc_value=15),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2998,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your spell critical damage bonus with all spells by $s1% but your non-periodic spell criticals cost an additional $s2% of the spell's cost.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 551686903, 'EffectSpellClassMaskA_2': 233544, 'EffectSpellClassMaskC_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 327680, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


fingers_of_frost_44543 = spell(
    id=44543,
    name='Fingers of Frost',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=44544),
    ],
    spell_icon_id=2947,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your Chill effects a $s1% chance to grant you the Fingers of Frost effect, which treats your next $44544s1 spells cast as if the target were Frozen.  Lasts $44544d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


fingers_of_frost_44545 = spell(
    id=44545,
    name='Fingers of Frost',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=44544),
    ],
    spell_icon_id=2947,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your Chill effects a $s1% chance to grant you the Fingers of Frost effect, which treats your next $44544s1 spells cast as if the target were Frozen.  Lasts $44544d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


brain_freeze_44546 = spell(
    id=44546,
    name='Brain Freeze',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=23, trigger_spell=57761),
    ],
    spell_icon_id=2938,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Frost damage spells with chilling effects have a $h% chance to cause your next Fireball or Frostfire Bolt spell to be instant cast and cost no mana.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 64, 'EffectSpellClassMaskA_2': 512, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 5, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


brain_freeze_44548 = spell(
    id=44548,
    name='Brain Freeze',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=23, trigger_spell=57761),
    ],
    spell_icon_id=2938,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Frost damage spells with chilling effects have a $h% chance to cause your next Fireball or Frostfire Bolt spell to be instant cast and cost no mana.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 64, 'EffectSpellClassMaskA_2': 512, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 10, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


brain_freeze_44549 = spell(
    id=44549,
    name='Brain Freeze',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=23, trigger_spell=57761),
    ],
    spell_icon_id=2938,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Frost damage spells with chilling effects have a $h% chance to cause your next Fireball or Frostfire Bolt spell to be instant cast and cost no mana.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 64, 'EffectSpellClassMaskA_2': 512, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 15, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


enduring_winter_44557 = spell(
    id=44557,
    name='Enduring Winter',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4999, implicit_target_a=1, apply_aura=107, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=8, trigger_spell=57669),
    ],
    spell_icon_id=2134,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 9, Enduring Winter). effect1's duration bonus (5/10/15s) already matched spec exactly but was completely unscoped in the pulled data (no EffectSpellClassMask at all on this effect) -- SpellInfo::IsAffected treats an all-zero classmask as matching every spell in the family, which would have extended the duration of every Mage aura-bearing spell, not just Summon Water Elemental. Scoped explicitly to word B = 2048, Summon Water Elemental's (31687) own identity flag. effect2 (Replenishment proc) needed zero changes -- matches spec exactly already, including the existing base spell_proc row's 6-sec ICE (confirmed pre-existing, not part of this migration).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the duration of your Summon Water Elemental spell by $/1000;s1 sec and your Frostbolt spell has a $h% chance to grant up to 10 party or raid members mana regeneration equal to 1% of their maximum mana per 5 sec for $57669d.  This effect cannot occur more often than once every $m2 sec. |cFF9D9D9DAt max rank, while your Water Elemental is active, each Frostbolt you cast extends its duration by 2 sec.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2048, 'EffectSpellClassMaskB_2': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 33, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskB_1': 2048},
)


enduring_winter_44560 = spell(
    id=44560,
    name='Enduring Winter',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9999, implicit_target_a=1, apply_aura=107, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=8, trigger_spell=57669),
    ],
    spell_icon_id=2134,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 9, Enduring Winter). effect1's duration bonus (5/10/15s) already matched spec exactly but was completely unscoped in the pulled data (no EffectSpellClassMask at all on this effect) -- SpellInfo::IsAffected treats an all-zero classmask as matching every spell in the family, which would have extended the duration of every Mage aura-bearing spell, not just Summon Water Elemental. Scoped explicitly to word B = 2048, Summon Water Elemental's (31687) own identity flag. effect2 (Replenishment proc) needed zero changes -- matches spec exactly already, including the existing base spell_proc row's 6-sec ICE (confirmed pre-existing, not part of this migration).",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the duration of your Summon Water Elemental spell by $/1000;s1 sec and your Frostbolt spell has a $h% chance to grant up to 10 party or raid members mana regeneration equal to 1% of their maximum mana per 5 sec for $57669d.  This effect cannot occur more often than once every $m2 sec. |cFF9D9D9DAt max rank, while your Water Elemental is active, each Frostbolt you cast extends its duration by 2 sec.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2048, 'EffectSpellClassMaskB_2': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 66, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskB_1': 2048},
)


enduring_winter_44561 = spell(
    id=44561,
    name='Enduring Winter',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14999, implicit_target_a=1, apply_aura=107, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=8, trigger_spell=57669),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2134,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 9, Enduring Winter). effect1's duration bonus (5/10/15s) already matched spec exactly but was completely unscoped in the pulled data (no EffectSpellClassMask at all on this effect) -- SpellInfo::IsAffected treats an all-zero classmask as matching every spell in the family, which would have extended the duration of every Mage aura-bearing spell, not just Summon Water Elemental. Scoped explicitly to word B = 2048, Summon Water Elemental's (31687) own identity flag. effect2 (Replenishment proc) needed zero changes -- matches spec exactly already, including the existing base spell_proc row's 6-sec ICE (confirmed pre-existing, not part of this migration). effect3 (rank 3 only, capstone): new SPELL_AURA_DUMMY read by spell_mage_enduring_winter (OnEffectProc, spell_mage.cpp) -- extends the caster's active Water Elemental's despawn timer by 2 sec per qualifying Frostbolt cast (TempSummon::SetTimer; Pet inherits this directly through Guardian/Minion/TempSummon). No-ops if the pet is the permanent-glyph variant (no despawn timer to extend) or not summoned at all.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the duration of your Summon Water Elemental spell by $/1000;s1 sec and your Frostbolt spell has a $h% chance to grant up to 10 party or raid members mana regeneration equal to 1% of their maximum mana per 5 sec for $57669d.  This effect cannot occur more often than once every $m2 sec.  While your Water Elemental is active, each Frostbolt you cast extends its duration by 2 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_2': 2048, 'EffectSpellClassMaskB_2': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskB_1': 2048},
)


chilled_to_the_bone_44566 = spell(
    id=44566,
    name='Chilled to the Bone',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=107, misc_value=3),
    ],
    spell_icon_id=2965,
    notes='pulled from existing data EffectSpellClassMaskA_2/B_1 override on effect index 1 (SPELLMOD_EFFECT1, -4/-7/-10, classmask 544 = Frostbolt|Cone of Cold) added on top of the pulled data to scope the movement- speed modifier to just those two spells. Playtest bugfix (2026-08-27, user report - "Permafrost reduces the effects of everything by 10%, not just move speed" - same root cause hit Chilled to the Bone too): the classmask was stored under EffectSpellClassMaskA_2, which spell_dbc/DBCStructure.h actually reads as effect index 0\'s second word, not effect index 1\'s first word - leaving effect 1\'s real classmask all-zero, which SpellInfo::IsAffected treats as matching every spell in the family. Moved to EffectSpellClassMaskB_1 (effect index 1(=B)\'s word 1), which is what the engine actually reads. See data/sql/updates/pending_db_world/frost_mage_rework.sql (merged Frost Mage rework migration; originally rev_1787820084006262155.sql) for the original diagnosis.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all damage you deal by $s1% and reduces the movement speed of targets affected by your Frostbolt, Cone of Cold and Frozen Orb by an additional $s2%. |cFF9D9D9DAt max rank, your Frostbolt and Ice Lance casts versus monsters reduce the cooldown of your Frozen Orb by 1 sec, and your Blizzard reduces it by 1 sec every 3 ticks.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 544, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


chilled_to_the_bone_44567 = spell(
    id=44567,
    name='Chilled to the Bone',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=-8, implicit_target_a=1, apply_aura=107, misc_value=3),
    ],
    spell_icon_id=2965,
    notes='pulled from existing data EffectSpellClassMaskA_2/B_1 override on effect index 1 (SPELLMOD_EFFECT1, -4/-7/-10, classmask 544 = Frostbolt|Cone of Cold) added on top of the pulled data to scope the movement- speed modifier to just those two spells. Playtest bugfix (2026-08-27, user report - "Permafrost reduces the effects of everything by 10%, not just move speed" - same root cause hit Chilled to the Bone too): the classmask was stored under EffectSpellClassMaskA_2, which spell_dbc/DBCStructure.h actually reads as effect index 0\'s second word, not effect index 1\'s first word - leaving effect 1\'s real classmask all-zero, which SpellInfo::IsAffected treats as matching every spell in the family. Moved to EffectSpellClassMaskB_1 (effect index 1(=B)\'s word 1), which is what the engine actually reads. See data/sql/updates/pending_db_world/frost_mage_rework.sql (merged Frost Mage rework migration; originally rev_1787820084006262155.sql) for the original diagnosis.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all damage you deal by $s1% and reduces the movement speed of targets affected by your Frostbolt, Cone of Cold and Frozen Orb by an additional $s2%. |cFF9D9D9DAt max rank, your Frostbolt and Ice Lance casts versus monsters reduce the cooldown of your Frozen Orb by 1 sec, and your Blizzard reduces it by 1 sec every 3 ticks.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 544, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


chilled_to_the_bone_44568 = spell(
    id=44568,
    name='Chilled to the Bone',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=107, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2965,
    notes='pulled from existing data EffectSpellClassMaskA_2/B_1 override on effect index 1 (SPELLMOD_EFFECT1, -4/-7/-10, classmask 544 = Frostbolt|Cone of Cold) added on top of the pulled data to scope the movement- speed modifier to just those two spells. Playtest bugfix (2026-08-27, user report - "Permafrost reduces the effects of everything by 10%, not just move speed" - same root cause hit Chilled to the Bone too): the classmask was stored under EffectSpellClassMaskA_2, which spell_dbc/DBCStructure.h actually reads as effect index 0\'s second word, not effect index 1\'s first word - leaving effect 1\'s real classmask all-zero, which SpellInfo::IsAffected treats as matching every spell in the family. Moved to EffectSpellClassMaskB_1 (effect index 1(=B)\'s word 1), which is what the engine actually reads. See data/sql/updates/pending_db_world/frost_mage_rework.sql (merged Frost Mage rework migration; originally rev_1787820084006262155.sql) for the original diagnosis.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all damage you deal by $s1% and reduces the movement speed of targets affected by your Frostbolt, Cone of Cold and Frozen Orb by an additional $s2%.  Your Frostbolt and Ice Lance casts versus monsters reduce the cooldown of your Frozen Orb by 1 sec, and your Blizzard reduces it by 1 sec every 3 ticks.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 544, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'AttributesEx3': 67633152, 'ProcChance': 100, 'ProcTypeMask': 327680, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


shattered_barrier_44745 = spell(
    id=44745,
    name='Shattered Barrier',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2945,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 7, Shattered Barrier). Old pulled data ('% chance to freeze all enemies when Ice Barrier is destroyed') is a different mechanic than the new spec entirely, not a retune -- rebuilt from scratch. effect1: SPELL_AURA_DUMMY (2/4%), read live in Mage::ApplyDoneDamagePctMods (MageMechanics.cpp) gated on caster->HasAura(Ice Barrier) -- same 'live armor-state check, not a static aura' idiom as Frost Warding's capstone, chosen for the same reason (Ice Barrier gets applied/consumed independently of this talent, a cached mod would go stale).",
    raw_overrides={'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While your Ice Barrier is active, your damage is increased by $s1%. |cFF9D9D9DAt max rank, your Ice Barrier shatters when destroyed, slowing all enemies within 10 yards by 70% for 4 sec and granting you 8% haste for 8 sec.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassSet': 3, 'SpellPriority': 50},
)


prismatic_cloak_54354 = spell(
    id=54354,
    name='Prismatic Cloak',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-7, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=-3001, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=2126,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces all damage taken by $s1% and reduces the fade time of your Invisibility spell by ${$m2/-1000} sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 538972160, 'EffectSpellClassMaskB_2': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


missile_barrage_54486 = spell(
    id=54486,
    name='Missile Barrage',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=44401),
    ],
    spell_icon_id=3261,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your Arcane Blast a $h% chance, and your Arcane Barrage, Fireball, Frostbolt and Frostfire Bolt spells a ${$h/2}% chance to reduce the channeled duration of the next Arcane Missiles spell by $44401s1%, reduce the mana cost by $44401s3%, and missiles will fire every .5 secs.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 23, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3},
)


missile_barrage_54488 = spell(
    id=54488,
    name='Missile Barrage',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=44401),
    ],
    spell_icon_id=3261,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your Arcane Blast a $h% chance, and your Arcane Barrage, Fireball, Frostbolt and Frostfire Bolt spells a ${$h/2}% chance to reduce the channeled duration of the next Arcane Missiles spell by $44401s1%, reduce the mana cost by $44401s3%, and missiles will fire every .5 secs.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 35, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3},
)


missile_barrage_54489 = spell(
    id=54489,
    name='Missile Barrage',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=44401),
    ],
    spell_icon_id=3261,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your Arcane Blast a $h% chance, and your Arcane Barrage, Fireball, Frostbolt and Frostfire Bolt spells a ${$h/2}% chance to reduce the channeled duration of the next Arcane Missiles spell by $44401s1%, reduce the mana cost by $44401s3%, and missiles will fire every .5 secs.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 32, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3},
)


missile_barrage_54490 = spell(
    id=54490,
    name='Missile Barrage',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=44401),
    ],
    spell_icon_id=3261,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your Arcane Blast a $h% chance, and your Arcane Barrage, Fireball, Frostbolt and Frostfire Bolt spells a ${$h/2}% chance to reduce the channeled duration of the next Arcane Missiles spell by $44401s1%, reduce the mana cost by $44401s3%, and missiles will fire every .5 secs.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 40, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 3},
)


incineration_54734 = spell(
    id=54734,
    name='Incineration',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-2000, die_sides=0, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COOLDOWN),
        Effect(type=EffectType.APPLY_AURA, base_points=30, die_sides=0, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=678,
    notes='Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (0,0) rank 3: absorbs the old Improved Fire Blast. Both SpellMods scoped to Fire Blast alone (dword-0 bit 0x2). No crit modifier on purpose - Fire Blast always crits (sec 3.1).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Fire Blast by 2 sec and increases its damage by 30%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'EffectSpellClassMaskB_1': 2},
)


burning_determination_54747 = spell(
    id=54747,
    name='Burning Determination',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=6971, trigger_spell=54748),
    ],
    spell_icon_id=2019,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AttributesEx7': 1073741824, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When Interrupted or Silenced you have a $h% chance to become immune to the next Interrupt or Silence mechanic.  Lasts $54748d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8388612, 'EffectSpellClassMaskA_2': 65536, 'EffectSpellClassMaskC_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'ProcTypeMask': 139808, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


burning_determination_54749 = spell(
    id=54749,
    name='Burning Determination',
    school=School.FIRE,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=6971, trigger_spell=54748),
    ],
    spell_icon_id=2019,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AttributesEx7': 1073741824, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When Interrupted or Silenced you have a $h% chance to become immune to the next Interrupt or Silence mechanic.  Lasts $54748d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8388612, 'EffectSpellClassMaskA_2': 65536, 'EffectSpellClassMaskC_1': 262144, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 139808, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


shattered_barrier_54787 = spell(
    id=54787,
    name='Shattered Barrier',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2945,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 7, Shattered Barrier). Old pulled data ('% chance to freeze all enemies when Ice Barrier is destroyed') is a different mechanic than the new spec entirely, not a retune -- rebuilt from scratch. effect1: SPELL_AURA_DUMMY (2/4%), read live in Mage::ApplyDoneDamagePctMods (MageMechanics.cpp) gated on caster->HasAura(Ice Barrier) -- same 'live armor-state check, not a static aura' idiom as Frost Warding's capstone, chosen for the same reason (Ice Barrier gets applied/consumed independently of this talent, a cached mod would go stale). effect2 (rank 2 only): capstone marker (SPELL_AURA_DUMMY, EFFECT_1), read by spell_mage_ice_barrier_aura's new AfterEffectAbsorb hook -- when the shield's remaining amount hits 0 (destroyed by damage, not merely expiring), casts a new AoE slow (200021, 10 yd, -70% for 4 sec) and a new self-haste buff (200022, 8%, 8 sec, same aura type as Icy Veins' own cast-speed effect).",
    raw_overrides={'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While your Ice Barrier is active, your damage is increased by $s1%.  Your Ice Barrier shatters when destroyed, slowing all enemies within 10 yards by 70% for 4 sec and granting you 8% haste for 8 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassSet': 3, 'SpellPriority': 50},
)


cold_as_ice_55091 = spell(
    id=55091,
    name='Cold as Ice',
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
    spell_icon_id=3260,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Cold Snap, Ice Barrier and Summon Water Elemental spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2053, 'EffectSpellClassMaskB_1': 576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3},
)


cold_as_ice_55092 = spell(
    id=55092,
    name='Cold as Ice',
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
    spell_icon_id=3260,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Cold Snap, Ice Barrier and Summon Water Elemental spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2053, 'EffectSpellClassMaskB_1': 576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3},
)


ice_floes_55094 = spell(
    id=55094,
    name='Ice Floes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-34, implicit_target_a=1, apply_aura=108, misc_value=11),
    ],
    spell_icon_id=2133,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Frost Nova, Cone of Cold, Ice Block and Icy Veins spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 576, 'EffectSpellClassMaskA_2': 16512, 'EffectSpellClassMaskB_1': 576, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3},
)


biting_cold_200010 = spell(
    id=200010,
    name='Biting Cold',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=189,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 2, Biting Cold): base effect only (the +2/4/6% Frost damage vs. chilled targets) - a SPELL_AURA_DUMMY read by a new SPELLFAMILY_MAGE case in Unit::SpellDamageBonusDone (Unit.cpp), matched by SpellIconID 189 (Spell_Frost_ChillingBolt) at EFFECT_0, same idiom as the Warlock/Hunter 'Torment the Weak' dummy lookup already in that function. 'Chilled' is read the same non-caster-scoped way Torment the Weak already does (Unit::HasAuraWithMechanic(MECHANIC_SNARE)) rather than a new caster-scoped check, for consistency with the existing idiom - see docs/frost-mage-talent-tree-handoff.md. The rank 3 capstone (bite a nearby chilled-enemy-triggered bounce) is a separate effect only on 200012, see that row's notes.",
    raw_overrides={'SpellClassSet': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Frost damage against targets affected by your chill effects is increased by 2%. |cFF9D9D9DAt max rank, dealing direct Frost damage to a chilled enemy has a 15% chance to bite into a nearby enemy within 8 yards, dealing Frost damage and chilling them. Cannot occur more than once every 6 sec.|r', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'SpellLevel': 1},
)


biting_cold_200011 = spell(
    id=200011,
    name='Biting Cold',
    school=School.FROST,
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
    spell_icon_id=189,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 2, Biting Cold): base effect only (the +2/4/6% Frost damage vs. chilled targets) - a SPELL_AURA_DUMMY read by a new SPELLFAMILY_MAGE case in Unit::SpellDamageBonusDone (Unit.cpp), matched by SpellIconID 189 (Spell_Frost_ChillingBolt) at EFFECT_0, same idiom as the Warlock/Hunter 'Torment the Weak' dummy lookup already in that function. 'Chilled' is read the same non-caster-scoped way Torment the Weak already does (Unit::HasAuraWithMechanic(MECHANIC_SNARE)) rather than a new caster-scoped check, for consistency with the existing idiom - see docs/frost-mage-talent-tree-handoff.md. The rank 3 capstone (bite a nearby chilled-enemy-triggered bounce) is a separate effect only on 200012, see that row's notes.",
    raw_overrides={'SpellClassSet': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Frost damage against targets affected by your chill effects is increased by 4%. |cFF9D9D9DAt max rank, dealing direct Frost damage to a chilled enemy has a 15% chance to bite into a nearby enemy within 8 yards, dealing Frost damage and chilling them. Cannot occur more than once every 6 sec.|r', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'SpellLevel': 1},
)


biting_cold_200012 = spell(
    id=200012,
    name='Biting Cold',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=200013),
    ],
    spell_icon_id=189,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 2, Biting Cold): base effect only (the +2/4/6% Frost damage vs. chilled targets) - a SPELL_AURA_DUMMY read by a new SPELLFAMILY_MAGE case in Unit::SpellDamageBonusDone (Unit.cpp), matched by SpellIconID 189 (Spell_Frost_ChillingBolt) at EFFECT_0, same idiom as the Warlock/Hunter 'Torment the Weak' dummy lookup already in that function. 'Chilled' is read the same non-caster-scoped way Torment the Weak already does (Unit::HasAuraWithMechanic(MECHANIC_SNARE)) rather than a new caster-scoped check, for consistency with the existing idiom - see docs/frost-mage-talent-tree-handoff.md. The rank 3 capstone (bite a nearby chilled-enemy-triggered bounce) is a separate effect only on 200012, see that row's notes. Capstone (EFFECT_1): apply_aura 42 = SPELL_AURA_PROC_TRIGGER_SPELL, trigger_spell 200013 (Icy Bite) - AttributesEx3/ProcTypeMask copied from Brain Freeze (44546), the same 'direct Frost/spell damage, not periodic' gate already proven elsewhere in this rework; ProcChance retuned to 15 (Brain Freeze's own 5 doesn't apply here). Script overrides the default trigger target (PreventDefaultAction) to pick a nearby enemy near the struck target instead of the struck target itself, gates on the target already being chilled, and enforces the 6 sec internal cooldown via a std::chrono::steady_clock member - same idiom as spell_pal_sacred_shield_dummy (spell_paladin.cpp).",
    raw_overrides={'SpellClassSet': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Frost damage against targets affected by your chill effects is increased by 6%. Dealing direct Frost damage to a chilled enemy has a 15% chance to bite into a nearby enemy within 8 yards, dealing Frost damage and chilling them. Cannot occur more than once every 6 sec.', 'EquippedItemClass': -1, 'ProcChance': 15, 'SpellPriority': 50, 'SpellLevel': 1, 'AttributesEx3': 67633152, 'ProcTypeMask': 65536},
)


icy_bite_200013 = spell(
    id=200013,
    name='Icy Bite',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=40.0,
    duration_ms=3000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=49, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, mechanic=Mechanic.SNARE, implicit_target_a=6, apply_aura=AuraType.MOD_HEALING_PCT, misc_value=127),
    ],
    spell_icon_id=189,
    coeff_weight=0.15,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 2, Biting Cold capstone). Triggered only (spell_mage_biting_cold, spell_mage.cpp) - never learned directly, same shape as Frozen Orb Pulse/Periodic (200008/200009). effect1: SPELL_EFFECT_SCHOOL_DAMAGE, 50 base + spell_bonus_data coeff_weight 0.15 (modest - a bonus proc, not a primary nuke; first-pass tuning value). effect2: SPELL_AURA_MOD_DECREASE_SPEED, mechanic 11 (MECHANIC_SNARE, matches Frostbolt's own slow so it also satisfies Unit::HasAuraWithMechanic(MECHANIC_SNARE) checks - including Biting Cold's own base effect), 20% slow for 3 sec, first-pass tuning value. Cast via caster->CastSpell(bounceTarget, 200013, true) so damage/threat attribute to the mage, not an unnamed source.",
    raw_overrides={'SpellClassSet': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Frost damage and a chill effect, bitten into a nearby enemy by Biting Cold.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'SpellLevel': 1, 'AuraDescription_Lang_enUS': 'Movement slowed by 30% and time between attacks increased by 25%.', 'AuraDescription_Lang_Mask': 16712190},
)


icy_shatter_200014 = spell(
    id=200014,
    name='Icy Shatter',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=1499, implicit_target_a=6),
    ],
    spell_icon_id=1236,
    coeff_weight=1.2,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 9 / sec 1 Glacial Spike, Arctic Winds capstone). Triggered only (spell_mage_glacial_spike::ConsumeIciclesAndFrostCharge, spell_mage.cpp) - never learned directly, same shape as Icy Bite (200013). Mirrors Glacial Spike's (200002) own damage exactly - 1500 base + 1.2 SP coeff (spell_bonus_data, same as 200002) - rather than re-triggering Glacial Spike itself against each additional target, which would re-run icicle/Fingers-of-Frost consumption per hit. Cast via caster->CastSpell(shatterTarget, 200014, true) for up to 5 nearby enemies within 8 yards, gated on Arctic Winds rank 3 (talent 1738, icon 2131 EFFECT_2).",
    raw_overrides={'SpellClassSet': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Frost damage, shattered onto a nearby enemy by Glacial Spike.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'SpellLevel': 1},
)


permafrost_200015 = spell(
    id=200015,
    name='Permafrost',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=143,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 2, Permafrost capstone). Triggered only (spell_mage_permafrost, spell_mage.cpp), granted once per second of continuous movement. Max 5 stacks (CumulativeAura). Duration bumped 3->10 sec (playtest bugfix, 2026-08-26): the original 3 sec first-pass guess decayed the whole stack before a mage could realistically stop and cast Ice Lance, making the bonus statistically undetectable in an actual playtest (5-stack vs 0-stack Ice Lance damage came back identical). 10 sec is a deliberate user call, not derived from the redesign text (which doesn't specify decay at all). Consumption also changed this pass: Ice Lance now clears the *entire* stack in one cast (spell_mage_ice_lance::ConsumePermafrost, RemoveAurasDueToSpell not ModStackAmount(-1)), and the damage bonus scales per stack consumed (20% * stack count, up to 100% at 5 stacks - Mage::ApplyDoneDamagePctMods) rather than a flat 20% regardless of banked stacks - both deliberate user calls resolving the ambiguity the previous notes flagged ('stacks read as banked charges... not fully disambiguated').",
    raw_overrides={'SpellClassSet': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your next Ice Lance by 20% per stack. Stacks up to 5 times, and are all consumed by your next Ice Lance.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'SpellLevel': 1, 'CumulativeAura': 5, 'AuraDescription_Lang_enUS': 'Increases the damage of your next Ice Lance by 20% per stack.', 'AuraDescription_Lang_Mask': 16712190},
)


frozen_core_200016 = spell(
    id=200016,
    name='Frozen Core',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=79, misc_value=16),
    ],
    spell_icon_id=2132,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 5, Frozen Core). Triggered only (native PROC_TRIGGER_SPELL on the talent's own 31667), granted on taking magic damage. One dedicated spell per rank rather than a shared spell with a scripted value, since each talent rank only ever triggers its own and the % doesn't need runtime computation.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Increases Frost damage dealt by 2%.', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases Frost damage dealt by 2%.', 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


frozen_core_200017 = spell(
    id=200017,
    name='Frozen Core',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=79, misc_value=16),
    ],
    spell_icon_id=2132,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 5, Frozen Core). Triggered only (native PROC_TRIGGER_SPELL on the talent's own 31668), granted on taking magic damage. One dedicated spell per rank rather than a shared spell with a scripted value, since each talent rank only ever triggers its own and the % doesn't need runtime computation.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Increases Frost damage dealt by 4%.', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases Frost damage dealt by 4%.', 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


frozen_core_200018 = spell(
    id=200018,
    name='Frozen Core',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=79, misc_value=16),
    ],
    spell_icon_id=2132,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 5, Frozen Core). Triggered only (native PROC_TRIGGER_SPELL on the talent's own 31669), granted on taking magic damage. One dedicated spell per rank rather than a shared spell with a scripted value, since each talent rank only ever triggers its own and the % doesn't need runtime computation.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Increases Frost damage dealt by 6%.', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases Frost damage dealt by 6%.', 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


frozen_core_piercing_cold_200019 = spell(
    id=200019,
    name='Frozen Core: Piercing Cold',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    range_yards=40.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=79, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=2000),
    ],
    spell_icon_id=2132,
    coeff_weight=0.05,
    notes='Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 5, Frozen Core capstone). Triggered only (spell_mage_frozen_core, spell_mage.cpp) on an Ice Lance critical strike against a frozen target. 80 base damage/tick (EffectBasePoints stored 79) + 0.05 SP coeff/tick (spell_bonus_data dot_bonus), 4 ticks over 8 sec -- modest, first-pass tuning value like this session\'s other new proc-only spells. \'Does not stack, refreshes on reapplication\' is free from native single-target same-spell-ID reapplication, no extra data needed. Playtest bugfix (2026-08-27, user call): range_yards was left blank, which reuse.py\'s range_index() defaults to RangeIndex 0 (self-only/no-range sentinel) - same root cause as the Shattering Cold bug found the same session. Since this is cast at the enemy target (not self), that silently blocked the DoT from ever landing. Set to 40 to match the other enemy-targeted triggered spells in this file (Glacial Spike, Shattering Cold, Flurry, Icy Bite/Shatter). Playtest bugfix #2 (2026-08-28, user call, "DoT lands on the caster, not the target"): effect1\'s implicit_target_a was 1 (TARGET_UNIT_CASTER/self) - wrong for an effect meant to land on the enemy target that caster->CastSpell(target, ...) in spell_mage_frozen_core (spell_mage.cpp) explicitly passes in; a self-implicit-target effect ignores the explicit CastSpell target and always resolves to the caster regardless. Set to 6 (TARGET_UNIT_TARGET_ENEMY) to match every other enemy-targeted triggered spell in this file.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': "Frost damage over time, pierced into the target's core.", 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Frost damage over time, pierced into the target's core.", 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


improved_cone_of_cold_200020 = spell(
    id=200020,
    name='Improved Cone of Cold',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=1, apply_aura=108, misc_value=19),
    ],
    spell_icon_id=35,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 6, Improved Cone of Cold capstone). Triggered only (native PROC_TRIGGER_SPELL on 12490, rank 3), granted after landing Cone of Cold. ProcCharges=1 so the native SpellMod charge system consumes it on the very next Blizzard cast (Player::ApplySpellMod) with no script needed; the 15-sec duration is just a safety window in case Blizzard is never cast, not a real balance number -- redesign text doesn't specify one, flagged for playtest.",
    raw_overrides={'SpellClassSet': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Blizzard channels twice as fast.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'SpellLevel': 1, 'EffectSpellClassMaskA_1': 524416, 'ProcCharges': 1, 'AuraDescription_Lang_enUS': 'Your Blizzard channels twice as fast.', 'AuraDescription_Lang_Mask': 16712190},
)


shattered_barrier_200021 = spell(
    id=200021,
    name='Shattered Barrier',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    radius_yards=10.0,
    duration_ms=4000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-71, mechanic=Mechanic.SNARE, implicit_target_a=6, apply_aura=AuraType.MOD_DECREASE_SPEED, radius_yards=10.0),
    ],
    spell_icon_id=2945,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 7, Shattered Barrier capstone). Triggered only (spell_mage_ice_barrier_aura::AfterEffectAbsorb, spell_mage.cpp), cast on the caster (TARGET_UNIT_SRC_AREA_ENEMY, implicit_target_a=6 -- same area-enemy shape as Frozen Orb Pulse/Icy Bite/Icy Shatter) when Ice Barrier's shield is destroyed by damage, not merely expiring. -70% movement speed for 4 sec, 10 yd radius, matches spec exactly.",
    raw_overrides={'SpellClassSet': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Movement speed reduced.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'SpellLevel': 1},
)


shattered_barrier_200022 = spell(
    id=200022,
    name='Shattered Barrier',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=65, misc_value=127),
    ],
    spell_icon_id=2945,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 7, Shattered Barrier capstone). Companion to 200021, same trigger. 8% for 8 sec -- reuses Icy Veins' own aura type (SPELL_AURA_MOD_CASTING_SPEED_NOT_STACK) for consistency ('haste' read as spell cast speed for a Mage, same as this project's other haste-flavored effects).",
    raw_overrides={'SpellClassSet': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases spell casting speed by 8%.', 'EquippedItemClass': -1, 'ProcChance': 101, 'SpellPriority': 50, 'SpellLevel': 1, 'AuraDescription_Lang_enUS': 'Increases spell casting speed by 8%.', 'AuraDescription_Lang_Mask': 16712190},
)


empowering_frostbolt_200023 = spell(
    id=200023,
    name='Empowering Frostbolt',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=108, misc_value=15),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=79, misc_value=16),
    ],
    spell_icon_id=188,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 8, Empowering Frostbolt). Triggered only (native PROC_TRIGGER_SPELL on 31682), granted after casting Frostbolt. effect1: ADD_PCT_MODIFIER/SPELLMOD_CRIT_DAMAGE_BONUS, empty classmask ('of your spells', same convention as Ice Shards/Winter's Chill's own broad crit-related effects). effect2: MOD_DAMAGE_PERCENT_DONE, Frost school mask. 8 sec, matches spec exactly.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Increases critical strike damage bonus and Frost damage dealt.', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases critical strike damage bonus and Frost damage dealt.', 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


empowering_frostbolt_200024 = spell(
    id=200024,
    name='Empowering Frostbolt',
    school=School.FROST,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=13, implicit_target_a=1, apply_aura=108, misc_value=15),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=79, misc_value=16),
    ],
    spell_icon_id=188,
    notes="Frost Mage rework (docs/frost-mage-redesign.md sec 4 Row 8, Empowering Frostbolt). Triggered only (native PROC_TRIGGER_SPELL on 31683), granted after casting Frostbolt. effect1: ADD_PCT_MODIFIER/SPELLMOD_CRIT_DAMAGE_BONUS, empty classmask ('of your spells', same convention as Ice Shards/Winter's Chill's own broad crit-related effects). effect2: MOD_DAMAGE_PERCENT_DONE, Frost school mask. 8 sec, matches spec exactly.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Increases critical strike damage bonus and Frost damage dealt.', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases critical strike damage bonus and Frost damage dealt.', 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


alacrity_200071 = spell(
    id=200071,
    name='Alacrity',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=306, misc_value=4194304),
    ],
    spell_icon_id=2022,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 0): Alacrity rank 3 - the stock Arcane Subtlety slot this talent reuses only had 2 ranks, so this rank is a newly-minted row (reserved block) rather than an edit to an existing spell.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Cooldown Haste by 15%.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


spellblade_200072 = spell(
    id=200072,
    name='Spellblade',
    school=School.ARCANE,
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
    spell_icon_id=3006,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 0): Spellblade shell only - "Your melee attacks have a 12% chance to restore 20% of your base mana and grant Replenishment. Capstone: weave melee attacks between casts with no reset." Deferred to Phase 3 in full (see the design doc\'s Deferred list): "20% of base mana" needs a live read (mana pools scale with gear, not just level - not DBC-expressible), and the capstone is a combat-mechanics change. This rank\'s row is a plain SPELL_AURA_DUMMY marker (SpellIconID 3006, unique to this talent) for Phase 3 to key off via GetAuraEffect(SPELL_AURA_DUMMY, SPELLFAMILY_MAGE, 3006, EFFECT_0) - no real proc wired yet. *Classless server only* per the design doc - this fork has no existing mechanism for gating a talent to one realm only; flagged for the user rather than guessed at.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your melee attacks have a 12% chance to restore 20% of your base mana and grant Replenishment.', 'ProcChance': 4, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'ProcTypeMask': 4, 'ProcCharges': 0},
)


spellblade_200073 = spell(
    id=200073,
    name='Spellblade',
    school=School.ARCANE,
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
    spell_icon_id=3006,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 0): Spellblade shell only - "Your melee attacks have a 12% chance to restore 20% of your base mana and grant Replenishment. Capstone: weave melee attacks between casts with no reset." Deferred to Phase 3 in full (see the design doc\'s Deferred list): "20% of base mana" needs a live read (mana pools scale with gear, not just level - not DBC-expressible), and the capstone is a combat-mechanics change. This rank\'s row is a plain SPELL_AURA_DUMMY marker (SpellIconID 3006, unique to this talent) for Phase 3 to key off via GetAuraEffect(SPELL_AURA_DUMMY, SPELLFAMILY_MAGE, 3006, EFFECT_0) - no real proc wired yet. *Classless server only* per the design doc - this fork has no existing mechanism for gating a talent to one realm only; flagged for the user rather than guessed at.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your melee attacks have a 12% chance to restore 20% of your base mana and grant Replenishment.', 'ProcChance': 8, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'ProcTypeMask': 4, 'ProcCharges': 0},
)


spellblade_200074 = spell(
    id=200074,
    name='Spellblade',
    school=School.ARCANE,
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
    spell_icon_id=3006,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 0): Spellblade shell only - "Your melee attacks have a 12% chance to restore 20% of your base mana and grant Replenishment. Capstone: weave melee attacks between casts with no reset." Deferred to Phase 3 in full (see the design doc\'s Deferred list): "20% of base mana" needs a live read (mana pools scale with gear, not just level - not DBC-expressible), and the capstone is a combat-mechanics change. This rank\'s row is a plain SPELL_AURA_DUMMY marker (SpellIconID 3006, unique to this talent) for Phase 3 to key off via GetAuraEffect(SPELL_AURA_DUMMY, SPELLFAMILY_MAGE, 3006, EFFECT_0) - no real proc wired yet. *Classless server only* per the design doc - this fork has no existing mechanism for gating a talent to one realm only; flagged for the user rather than guessed at.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your melee attacks have a 12% chance to restore 20% of your base mana and grant Replenishment.', 'ProcChance': 12, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'ProcTypeMask': 4, 'ProcCharges': 0},
)


magic_absorption_200075 = spell(
    id=200075,
    name='Magic Absorption',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=79, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=44, implicit_target_a=1, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=459,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 1): Magic Absorption rank 3 - the stock talent this reuses (id 1650) only had 2 ranks, so this rank is a newly-minted row rather than an edit to an existing spell.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all magic damage done by 3% and reduces all magic damage taken by 3%. Increases the mana you gain from Mana Gems by 45%.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskA_3': 16},
)


arcane_concentration_200076 = spell(
    id=200076,
    name='Arcane Concentration',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=12536),
    ],
    spell_icon_id=212,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 2): Arcane Concentration rank 3 - the stock talent this reuses (id 82, Magic Attunement) only had 2 ranks, so this rank is a newly-minted row rather than an edit to an existing spell.',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives you a 15% chance of entering a Clearcasting state after casting a damaging spell.', 'ProcChance': 15, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


magic_attunement_28574 = spell(
    id=28574,
    name='Magic Attunement',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=108, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=-15001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=1880,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 2): repoints stock talent id 85 (never pulled in before) to (2,1), trimmed to 2 ranks (54659 orphaned). "Increases the effect of your Amplify Magic and Dampen Magic spells by 25/50% and reduces their cooldown by 15/30 seconds." Both spells (1008, 604) share SpellClassMask_1 8192 (verified live via the DB overlay). effect1 SPELL_AURA_ADD_PCT_MODIFIER (108)/SPELLMOD_EFFECT1 (3), effect2 SPELL_AURA_ADD_FLAT_MODIFIER (107)/SPELLMOD_COOLDOWN (11), both with EffectSpellClassMaskA_1 = 8192 in raw_overrides. Fresh row - id 28574/54658 had never been pulled into any source CSV before (an earlier pass of this edit tried to edit a row that didn\'t exist yet, a silent no-op; caught by checking the generated SQL for these IDs and finding them absent, fixed by adding them as new rows instead).',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effect of your Amplify Magic and Dampen Magic spells by 25% and reduces their cooldown by 15 seconds.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': 8192, 'EffectSpellClassMaskB_1': 8192},
)


magic_attunement_54658 = spell(
    id=54658,
    name='Magic Attunement',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=108, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=-30001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=1880,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 2): repoints stock talent id 85 (never pulled in before) to (2,1), trimmed to 2 ranks (54659 orphaned). "Increases the effect of your Amplify Magic and Dampen Magic spells by 25/50% and reduces their cooldown by 15/30 seconds." Both spells (1008, 604) share SpellClassMask_1 8192 (verified live via the DB overlay). effect1 SPELL_AURA_ADD_PCT_MODIFIER (108)/SPELLMOD_EFFECT1 (3), effect2 SPELL_AURA_ADD_FLAT_MODIFIER (107)/SPELLMOD_COOLDOWN (11), both with EffectSpellClassMaskA_1 = 8192 in raw_overrides. Fresh row - id 28574/54658 had never been pulled into any source CSV before (an earlier pass of this edit tried to edit a row that didn\'t exist yet, a silent no-op; caught by checking the generated SQL for these IDs and finding them absent, fixed by adding them as new rows instead).',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effect of your Amplify Magic and Dampen Magic spells by 50% and reduces their cooldown by 30 seconds.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': 8192, 'EffectSpellClassMaskB_1': 8192},
)


student_of_the_mind_44397 = spell(
    id=44397,
    name='Student of the Mind',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=219, misc_value=3),
    ],
    spell_icon_id=1873,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 2): repoints stock talent id 1845 (never pulled in) to (2,2), same rank count. "You regenerate mana equal to 5/10/15% of your Intellect every 5 seconds. This regeneration continues while casting." Fully data-only - SPELL_AURA_MOD_MANA_REGEN_FROM_STAT (219), misc_value STAT_INTELLECT (3); Player::UpdateManaRegen() (StatSystem.cpp) computes GetStat(stat) * Amount / 500 as flat mp5 and applies it unconditionally to both the normal and while-casting regen fields - no live check/script needed. Fresh row - id 44397/44398/44399 had never been pulled into any source CSV before (an earlier pass of this edit tried to edit rows that didn\'t exist yet, a silent no-op; caught and fixed the same way as Magic Attunement above).',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You regenerate mana equal to 5% of your Intellect every 5 sec. This regeneration continues while casting.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


student_of_the_mind_44398 = spell(
    id=44398,
    name='Student of the Mind',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=219, misc_value=3),
    ],
    spell_icon_id=1873,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 2): repoints stock talent id 1845 (never pulled in) to (2,2), same rank count. "You regenerate mana equal to 5/10/15% of your Intellect every 5 seconds. This regeneration continues while casting." Fully data-only - SPELL_AURA_MOD_MANA_REGEN_FROM_STAT (219), misc_value STAT_INTELLECT (3); Player::UpdateManaRegen() (StatSystem.cpp) computes GetStat(stat) * Amount / 500 as flat mp5 and applies it unconditionally to both the normal and while-casting regen fields - no live check/script needed. Fresh row - id 44397/44398/44399 had never been pulled into any source CSV before (an earlier pass of this edit tried to edit rows that didn\'t exist yet, a silent no-op; caught and fixed the same way as Magic Attunement above).',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You regenerate mana equal to 10% of your Intellect every 5 sec. This regeneration continues while casting.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


student_of_the_mind_44399 = spell(
    id=44399,
    name='Student of the Mind',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=74, implicit_target_a=1, apply_aura=219, misc_value=3),
    ],
    spell_icon_id=1873,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 2): repoints stock talent id 1845 (never pulled in) to (2,2), same rank count. "You regenerate mana equal to 5/10/15% of your Intellect every 5 seconds. This regeneration continues while casting." Fully data-only - SPELL_AURA_MOD_MANA_REGEN_FROM_STAT (219), misc_value STAT_INTELLECT (3); Player::UpdateManaRegen() (StatSystem.cpp) computes GetStat(stat) * Amount / 500 as flat mp5 and applies it unconditionally to both the normal and while-casting regen fields - no live check/script needed. Fresh row - id 44397/44398/44399 had never been pulled into any source CSV before (an earlier pass of this edit tried to edit rows that didn\'t exist yet, a silent no-op; caught and fixed the same way as Magic Attunement above).',
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You regenerate mana equal to 15% of your Intellect every 5 sec. This regeneration continues while casting.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


arcane_resonance_18462 = spell(
    id=18462,
    name='Arcane Resonance',
    school=School.ARCANE,
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
    spell_icon_id=3007,
    notes="Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 3): repoints stock talent id 1142 (never pulled in) to (3,2). Whole talent deferred to Phase 3 (see the design doc's Deferred list) - needs a live 4-stacks-of-Arcane-Blast read at damage-calc time, mirroring Frost's Frostbite/Ice Shards MageMechanics pattern. Shell only: SPELL_AURA_DUMMY marker (SpellIconID 3007) per SKILL.md Phase 3's marker-aura-by-icon idiom. Fresh row - id 18462/18463/18464 had never been pulled into any source CSV before (same silent-no-op bug as Magic Attunement/Student of the Mind above, caught and fixed).",
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While you have 4 stacks of Arcane Blast, your Arcane damage is increased by $s1%. Spells that consume your Arcane Blast stacks benefit from this bonus.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


arcane_resonance_18463 = spell(
    id=18463,
    name='Arcane Resonance',
    school=School.ARCANE,
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
    spell_icon_id=3007,
    notes="Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 3): repoints stock talent id 1142 (never pulled in) to (3,2). Whole talent deferred to Phase 3 (see the design doc's Deferred list) - needs a live 4-stacks-of-Arcane-Blast read at damage-calc time, mirroring Frost's Frostbite/Ice Shards MageMechanics pattern. Shell only: SPELL_AURA_DUMMY marker (SpellIconID 3007) per SKILL.md Phase 3's marker-aura-by-icon idiom. Fresh row - id 18462/18463/18464 had never been pulled into any source CSV before (same silent-no-op bug as Magic Attunement/Student of the Mind above, caught and fixed).",
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While you have 4 stacks of Arcane Blast, your Arcane damage is increased by $s1%. Spells that consume your Arcane Blast stacks benefit from this bonus.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


arcane_resonance_18464 = spell(
    id=18464,
    name='Arcane Resonance',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3007,
    notes="Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 3): repoints stock talent id 1142 (never pulled in) to (3,2). Whole talent deferred to Phase 3 (see the design doc's Deferred list) - needs a live 4-stacks-of-Arcane-Blast read at damage-calc time, mirroring Frost's Frostbite/Ice Shards MageMechanics pattern. Shell only: SPELL_AURA_DUMMY marker (SpellIconID 3007) per SKILL.md Phase 3's marker-aura-by-icon idiom. Fresh row - id 18462/18463/18464 had never been pulled into any source CSV before (same silent-no-op bug as Magic Attunement/Student of the Mind above, caught and fixed).",
    raw_overrides={'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While you have 4 stacks of Arcane Blast, your Arcane damage is increased by $s1%. Spells that consume your Arcane Blast stacks benefit from this bonus.', 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50},
)


arcane_mind_11232 = spell(
    id=11232,
    name='Arcane Mind',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=137, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=71,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Intellect by $s1%. Your magic damage is increased by up to $s2%, scaling with your current mana percentage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellLevel': 1, 'SpellPriority': 50},
)


arcane_mind_12500 = spell(
    id=12500,
    name='Arcane Mind',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=137, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=71,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Intellect by $s1%. Your magic damage is increased by up to $s2%, scaling with your current mana percentage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellLevel': 1, 'SpellPriority': 50},
)


arcane_mind_12501 = spell(
    id=12501,
    name='Arcane Mind',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=137, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=71,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Intellect by $s1%. Your magic damage is increased by up to $s2%, scaling with your current mana percentage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellLevel': 1, 'SpellPriority': 50},
)


arcane_mind_12502 = spell(
    id=12502,
    name='Arcane Mind',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=137, misc_value=3),
    ],
    spell_icon_id=71,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Intellect by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellLevel': 1, 'SpellPriority': 50},
)


arcane_mind_12503 = spell(
    id=12503,
    name='Arcane Mind',
    school=School.ARCANE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=137, misc_value=3),
    ],
    spell_icon_id=71,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Intellect by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellLevel': 1, 'SpellPriority': 50},
)


incanter_s_absorption_44394 = spell(
    id=44394,
    name="Incanter's Absorption",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.DUMMY, trigger_spell=44413),
        Effect(type=EffectType.APPLY_AURA, base_points=-1001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=2941,
    notes='pulled from existing data | Bugfix (playtest report, 2026-09-08): Description_Lang_enUS still read as the unmodified real-game tooltip ("does not have the right tooltip and looks like its the old version") even though Phase 2/3 added the Spellsteal CD (effect2) and shield-grant proc (spell_mage_incanters_absorption_shield, spell_mage.cpp) on top of the pre-existing ward-absorb clause (kept working, untouched) - text now describes all three.',
    raw_overrides={'AttributesEx3': 67108864, 'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When your Mana Shield, Frost Ward, Fire Ward, or Ice Barrier absorbs damage your spell damage is increased by $s1% of the amount absorbed for $44413d. Reduces the cooldown of Spellsteal by 1 sec. Casting a direct damaging Arcane spell with a cast time, or Arcane Missiles while Missile Barrage is active, grants you a shield that absorbs a small amount of damage.\n\n|cFF9D9D9DCapstone Bonus: Your Spellsteal also steals an additional spell from the target.|r', 'DurationIndex': 0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_2': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'RangeIndex': 1, 'ProcTypeMask': 65536, 'ProcCharges': 0},
)


incanter_s_absorption_44395 = spell(
    id=44395,
    name="Incanter's Absorption",
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
        Effect(type=EffectType.APPLY_AURA, base_points=-2001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=2941,
    notes="pulled from existing data | Bugfix (playtest report, 2026-09-08): Description_Lang_enUS now describes the Spellsteal CD (effect2) and shield-grant proc alongside the pre-existing ward-absorb clause - see 44394's note.",
    raw_overrides={'AttributesEx3': 67108864, 'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When your Mana Shield, Frost Ward, Fire Ward, or Ice Barrier absorbs damage your spell damage is increased by $s1% of the amount absorbed for $44413d. Reduces the cooldown of Spellsteal by 2 sec. Casting a direct damaging Arcane spell with a cast time, or Arcane Missiles while Missile Barrage is active, grants you a shield that absorbs a small amount of damage.\n\n|cFF9D9D9DCapstone Bonus: Your Spellsteal also steals an additional spell from the target.|r', 'DurationIndex': 0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_2': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'RangeIndex': 1, 'ProcTypeMask': 65536, 'ProcCharges': 0},
)


incanter_s_absorption_44396 = spell(
    id=44396,
    name="Incanter's Absorption",
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
        Effect(type=EffectType.APPLY_AURA, base_points=-3001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2941,
    notes="pulled from existing data | Bugfix (playtest report, 2026-09-08): Description_Lang_enUS now describes the Spellsteal CD (effect2), shield-grant proc, and rank-3 capstone (effect3 marker, read by spell_mage_spellsteal for an extra steal) alongside the pre-existing ward-absorb clause - see 44394's note.",
    raw_overrides={'AttributesEx3': 67108864, 'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When your Mana Shield, Frost Ward, Fire Ward, or Ice Barrier absorbs damage your spell damage is increased by $s1% of the amount absorbed for $44413d. Reduces the cooldown of Spellsteal by 3 sec. Casting a direct damaging Arcane spell with a cast time, or Arcane Missiles while Missile Barrage is active, grants you a shield that absorbs a small amount of damage.\n\nCapstone Bonus: Your Spellsteal also steals an additional spell from the target.', 'DurationIndex': 0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_2': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'RangeIndex': 1, 'ProcTypeMask': 65536, 'ProcCharges': 0},
)


spell_power_200077 = spell(
    id=200077,
    name='Spell Power',
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
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2281,
    notes="Arcane Mage rework (docs/arcane-mage-rework-design.md, Row 4) - new spell, 3rd rank of Spell Power (id 1826), minted from source/ids.yaml's reserved spell block. Mirrors ranks 1-2's structure exactly.",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases critical strike damage bonus of all spells by $s1%.\n\nCapstone Bonus: Dealing direct critical damage with a spell while your mana is below 50% taps into raw power, restoring 1% of your total mana each second and increasing your magic damage by 10% and Arcane damage by another 5%. This effect lasts for 10 seconds and can only occur once every 30 seconds.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 551686903, 'EffectSpellClassMaskA_2': 102472, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellLevel': 1, 'SpellPriority': 50, 'ProcTypeMask': 65536, 'ProcCharges': 0},
)


spell_power_200080 = spell(
    id=200080,
    name='Spell Power',
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PERIODIC_ENERGIZE, amplitude=1000),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=79, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=79, misc_value=64),
    ],
    spell_icon_id=2281,
    notes="Arcane Mage rework (docs/arcane-mage-rework-design.md, Phase 3 Batch B) - Spell Power's (4,0) capstone buff, granted by spell_mage_spell_power_capstone (spell_mage.cpp) on a direct spell crit while below 50% mana, ICD 30s. effect1's mana-per-second amount is computed live from the caster's max mana at grant time (same CastCustomSpell idiom as spell_mage_magic_absorption), not a live per-tick read - matches the design's 'restoring 1% of your total mana each second' as a snapshot at proc time, not a moving target.",
    raw_overrides={'BaseLevel': 80, 'SpellLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Restoring 1% of your total mana each second, and your magic damage is increased by 10% (Arcane damage by an additional 5%).', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Restoring 1% of your total mana each second, and your magic damage is increased by 10% (Arcane damage by an additional 5%).'},
)


improved_blink_200081 = spell(
    id=200081,
    name='Improved Blink',
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    duration_ms=3000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
    ],
    spell_icon_id=1499,
    notes="Arcane Mage rework (docs/arcane-mage-rework-design.md, Phase 3 Batch B) - Improved Blink's (4,2) capstone buff, granted by spell_mage_blink (spell_mage.cpp) after casting Blink (1953), rank 2 only.",
    raw_overrides={'BaseLevel': 80, 'SpellLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'All damage taken is reduced by 20%.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage taken reduced.'},
)


arcane_shielding_200082 = spell(
    id=200082,
    name='Arcane Shielding',
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=79, misc_value=127),
    ],
    spell_icon_id=209,
    notes="Arcane Mage rework (docs/arcane-mage-rework-design.md, Phase 3 Batch B) - Arcane Shielding's (3,0) rank 1 proc buff, granted by spell_mage_arcane_shielding_proc (spell_mage.cpp) each time Fire Ward/Frost Ward/Arcane Ward absorbs damage - same AfterEffectAbsorb hook as Incanter's Absorption's existing base script, shared spell_script_names row.",
    raw_overrides={'BaseLevel': 80, 'SpellLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Damage dealt increased by 5%.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage dealt increased.'},
)


arcane_shielding_200083 = spell(
    id=200083,
    name='Arcane Shielding',
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=79, misc_value=127),
    ],
    spell_icon_id=209,
    notes="Arcane Mage rework (docs/arcane-mage-rework-design.md, Phase 3 Batch B) - Arcane Shielding's (3,0) rank 2 proc buff - see 200082's notes.",
    raw_overrides={'BaseLevel': 80, 'SpellLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Damage dealt increased by 10%.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage dealt increased.'},
)


improved_counterspell_200084 = spell(
    id=200084,
    name='Improved Counterspell',
    school=School.ARCANE,
    mechanic=Mechanic.SILENCE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    duration_ms=2000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, mechanic=Mechanic.SILENCE, implicit_target_a=6, apply_aura=AuraType.MOD_SILENCE),
    ],
    spell_icon_id=17,
    notes="Arcane Mage rework (docs/arcane-mage-rework-design.md, Phase 3 Batch B) - Improved Counterspell's (3,1) capstone debuff, cast on Counterspell's (2139) target by spell_mage_counterspell (spell_mage.cpp) when the caster has rank 2's marker - a new debuff rather than a raw Counterspell DBC edit, so players without the talent aren't silenced.",
    raw_overrides={'BaseLevel': 80, 'SpellLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Silenced.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Silenced.'},
)


arcane_mastery_200085 = spell(
    id=200085,
    name='Arcane Mastery',
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    duration_ms=1500,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1976,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Phase 3 Batch C) - shared marker for Arcane Concentration\'s (2,0) and Missile Barrage\'s (5,0) Mastery clause (System Rulings: one shared hook). base_points computed live at grant time (player->GetMasteryPercentage() * 0.5, matching System Rulings\' "roughly half the coefficient of Fire\'s/Frost\'s single hook" - Frost\'s own Frostbite capstone applies GetMasteryPercentage() at full weight, unscaled), read in MageMechanics.cpp::ApplyDoneDamagePctMods. die_sides=0 so the CastCustomSpell-injected value is used exactly as passed.',
    raw_overrides={'BaseLevel': 80, 'SpellLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Damage of your next spell increased by your Mastery.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Empowered by Mastery.'},
)


incanter_s_absorption_200086 = spell(
    id=200086,
    name="Incanter's Absorption",
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=69, misc_value=127),
    ],
    spell_icon_id=2941,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Phase 3 Batch C) - Incanter\'s Absorption\'s (6,2) new "100% chance to grant a shield" proc, granted by spell_mage_incanters_absorption_shield (spell_mage.cpp) off a cast-time-bearing Arcane spell or Arcane Missiles while Missile Barrage is active. Absorb amount computed live at grant time (caster->SpellBaseDamageBonusDone(SPELL_SCHOOL_MASK_ARCANE) * 0.15, a placeholder coefficient - \'a small amount\', flagged for Phase 4 playtest tuning same as Arcane Overload\'s own coefficient). die_sides=0 so the CastCustomSpell-injected value is used exactly as passed. Separate from the existing ward-absorb-scaling mechanism (spell_mage_incanters_absorbtion_base_AuraScript) - that one is untouched.',
    raw_overrides={'BaseLevel': 80, 'SpellLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Absorbs a small amount of damage.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Shielded.'},
)


spellblade_200087 = spell(
    id=200087,
    name='Spellblade',
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    effects=[
        Effect(type=EffectType.ENERGIZE, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=3006,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Phase 3 Batch C) - Spellblade\'s (0,3) mana-restore clause, granted by spell_mage_spellblade (spell_mage.cpp) on a melee auto-attack proc (native ProcTypeMask 4/rank-scaled ProcChance added to 200072-200074 this batch). SPELL_EFFECT_ENERGIZE (type 30, flat amount, not the %-based ENERGIZE_PCT=137) - base_points computed live via CalculatePct(caster->GetCreateMana(), 20) (GetCreateMana() = UNIT_FIELD_BASE_MANA, the class/level base pool before Intellect scaling - matches "20% of your BASE mana" literally, distinct from max/missing mana used elsewhere in this rework). Replenishment (real stock 57669) is cast separately, alongside this, straight off its own native raid-AOE targeting (same TARGET_UNIT_CASTER_AREA_RAID/100yd shape as Brilliance Aura) - no new spell needed for that half of the clause.',
    raw_overrides={'BaseLevel': 80, 'SpellLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Restores mana.'},
)


netherwind_presence_200088 = spell(
    id=200088,
    name='Netherwind Presence',
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=65),
    ],
    spell_icon_id=2943,
    notes="Arcane Mage rework (docs/arcane-mage-rework-design.md, Phase 3 Batch D) - Netherwind Presence's (9,1) stacking haste buff, granted by spell_mage_netherwind_presence (spell_mage.cpp) off casting Arcane Missiles/Barrage/Blast/Starfire/Moonfire (Arcane Orb/Starsurge omitted - don't exist in this WotLK ruleset). CumulativeAura=3 (max stack) - the engine multiplies base_points by current stack count natively, same idiom as Frost's own Permafrost stacks.",
    raw_overrides={'BaseLevel': 80, 'SpellLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'CumulativeAura': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your haste by $s1%, stacking up to 3 times.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Haste increased by $s1%.'},
)


netherwind_presence_200089 = spell(
    id=200089,
    name='Netherwind Presence',
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=65),
    ],
    spell_icon_id=2943,
    notes="Arcane Mage rework (docs/arcane-mage-rework-design.md, Phase 3 Batch D) - Netherwind Presence's (9,1) stacking haste buff, granted by spell_mage_netherwind_presence (spell_mage.cpp) off casting Arcane Missiles/Barrage/Blast/Starfire/Moonfire (Arcane Orb/Starsurge omitted - don't exist in this WotLK ruleset). CumulativeAura=3 (max stack) - the engine multiplies base_points by current stack count natively, same idiom as Frost's own Permafrost stacks.",
    raw_overrides={'BaseLevel': 80, 'SpellLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'CumulativeAura': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your haste by $s1%, stacking up to 3 times.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Haste increased by $s1%.'},
)


netherwind_presence_200090 = spell(
    id=200090,
    name='Netherwind Presence',
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=65),
    ],
    spell_icon_id=2943,
    notes="Arcane Mage rework (docs/arcane-mage-rework-design.md, Phase 3 Batch D) - Netherwind Presence's (9,1) stacking haste buff, granted by spell_mage_netherwind_presence (spell_mage.cpp) off casting Arcane Missiles/Barrage/Blast/Starfire/Moonfire (Arcane Orb/Starsurge omitted - don't exist in this WotLK ruleset). CumulativeAura=3 (max stack) - the engine multiplies base_points by current stack count natively, same idiom as Frost's own Permafrost stacks.",
    raw_overrides={'BaseLevel': 80, 'SpellLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'CumulativeAura': 3, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your haste by $s1%, stacking up to 3 times.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Haste increased by $s1%.'},
)


netherwind_presence_200091 = spell(
    id=200091,
    name='Netherwind Presence',
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2943,
    notes='Arcane Mage rework (docs/arcane-mage-rework-design.md, Phase 3 Batch D) - Netherwind Presence capstone\'s internal cooldown marker ("cannot occur more than once every 30 sec"), applied to self by spell_mage_slow and checked via HasAura() before re-triggering. AttributesEx 131072 hides it from the buff bar, same flag already used on Brilliance Aura/Time Warp for their own utility auras.',
    raw_overrides={'AttributesEx': 131072, 'BaseLevel': 80, 'SpellLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190},
)


arcane_overload_200092 = spell(
    id=200092,
    name='Arcane Overload',
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, die_sides=0, implicit_target_a=6, misc_value=6),
    ],
    spell_icon_id=2210,
    notes="Bugfix (playtest report, 2026-09-08) - implicit_target_a was 1 (TARGET_UNIT_CASTER), a leftover default that made this sub-spell always hit the caster instead of the passed CastCustomSpell target ('Arcane Overload deals damage to you and not the target'); fixed to 6 (TARGET_UNIT_TARGET_ENEMY). misc_value (the SPELL_EFFECT_SCHOOL_DAMAGE school index, 0=Physical/6=Arcane - distinct from the row's own SchoolMask column, which was already 64/Arcane) was left at its 0 default, so the hit rolled as Physical damage ('needs to be in the Arcane School'); fixed to 6. Original note: Arcane Mage rework (docs/arcane-mage-rework-design.md, Phase 3 Batch D) - Arcane Overload's (10,1) actual damage-dealing sub-spell, hit once per target (primary + AoE-around-caster, apps/dbc-tools' own 200079 effect2) by spell_mage_arcane_overload. die_sides=0 so the CastCustomSpell-injected value (mana spent + placeholder spell power coefficient, with falloff beyond 5 targets) is used exactly as passed.",
    raw_overrides={'BaseLevel': 80, 'SpellLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 6, 'SpellClassSet': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Arcane damage.', 'SpellClassMask_3': 2},
)


arcane_overload_200093 = spell(
    id=200093,
    name='Arcane Overload',
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PERIODIC_ENERGIZE, amplitude=1000),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=79, misc_value=126),
    ],
    spell_icon_id=2210,
    notes="Arcane Mage rework (docs/arcane-mage-rework-design.md, Phase 3 Batch D) - Arcane Overload's (10,1) 15s follow-up buff, granted by spell_mage_arcane_overload after the damage resolves.",
    raw_overrides={'BaseLevel': 80, 'SpellLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Restoring 3% of your maximum mana every 1 sec, and your spell damage is increased by 10%.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Rapidly regenerating mana.'},
)


netherwind_presence_200094 = spell(
    id=200094,
    name='Netherwind Presence',
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=AuraType.MOD_INCREASE_SPEED),
    ],
    spell_icon_id=2943,
    notes="Arcane Mage rework (docs/arcane-mage-rework-design.md, Phase 3 Batch D) - Netherwind Presence's (9,1) capstone speed buff, granted by spell_mage_slow when Slow is cast while fully stacked (rank 3 only), gated by a 30s ICD (200091).",
    raw_overrides={'BaseLevel': 80, 'SpellLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Movement speed increased by 50%.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement speed increased.'},
)


# ---------------------------------------------------------------------------------------------
# Fire Mage rework (docs/reworks/fire-mage-rework.md) - Phase 1: new systems. See mage_spells.py's
# "Fire Mage rework" block for the custom SpellClassMask_3 bit assignments.
# ---------------------------------------------------------------------------------------------

meteor_impact_200096 = spell(
    id=200096,
    name='Meteor',
    school=School.FIRE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=40.0,
    radius_yards=8.0,
    duration_ms=4000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=751, points_per_level=14.1, die_sides=41, implicit_target_a=16, radius_yards=8.0),
        Effect(type=EffectType.PERSISTENT_AREA_AURA, base_points=160, points_per_level=3.3, implicit_target_a=28, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=1000, radius_yards=8.0),
    ],
    spell_icon_id=1516,
    notes="Fire Mage rework sec 2 - Meteor's impact + ground burn, cast by spell_mage_meteor 3 sec after the player's Meteor (200095). Same shape as Flamestrike (2120): effect1 direct damage to every enemy in the 8yd area, effect2 a 4-sec persistent ground aura ticking every 1 sec. Budget (user call, 2026-09-15): ~2x Flamestrike - direct 751+14.1/lvl (die 41) vs Flamestrike's 51+7.4955/lvl anchored at Meteor's own SpellLevel 58, so ~780 at 60 / ~1060 at 80 vs Flamestrike's ~381 / ~531; burn 160+3.3/lvl per 1-sec tick x4 vs Flamestrike's 84->117 per 2-sec tick x4. Coefficients (spec: 0.3 direct / 0.15 burn) are in spell_bonus_data via bonus_coefficients() in mage_spells.py - dot_bonus is applied PER TICK by Unit::SpellDamageBonusDone, the same convention Flamestrike's own 0.122 row uses. Only the impact can crit -> only the impact banks Ignite (sec 4.1a); the burn is periodic and never does. SpellVisualID_1 90003 (patch_mage_vfx_models.py) - superseded the earlier Flamestrike reuse (10383) now that a purpose-built Ascension model exists: InstantAreaKit + PersistentAreaKit both point at the same kit wrapping mage_meteor_impactstate_world, so the burst and the 4-sec ground-burn's own visual are the same asset (its name suggests it's already a combined burst+decal, not two separate assets - see docs/reworks/fire-mage-meteor-vfx.md).",
    raw_overrides={'BaseLevel': 58, 'SpellLevel': 58, 'MaxLevel': 80, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 3, 'SpellClassMask_3': 32, 'SpellPriority': 50, 'SpellVisualID_1': 90003, 'Targets': 64, 'AttributesEx': 268435592, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Deals $s1 Fire damage to all enemies in the area and burns the ground for $o2 Fire damage over $d.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s2 Fire damage every $t2 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


kindling_200097 = spell(
    id=200097,
    name='Kindling',
    school=School.FIRE,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=292,
    notes="Fire Mage rework sec 4.2 - Kindling. Stacking buff on the mage (CumulativeAura 25), each stack +9% Blast Wave damage via a SPELLMOD_DAMAGE scoped to Blast Wave's own classmask bit (Effect_1 -> EffectSpellClassMaskA_2 = 64, the dword Blast Wave 11113 carries SpellClassMask_2 = 64 in) - AuraEffect::CalculateAmount multiplies by stack count, so 25 stacks = +225%. Granted by Mage::GrantKindling() (Tinderbox's Ignite-tick roll, Impact Crater's Meteor hits), consumed entirely by spell_mage_blast_wave after the cast's damage is calculated. No duration ('until consumed'), no internal cooldown - the stack cap is the throttle. Icon 292 = Blast Wave's own.",
    raw_overrides={'BaseLevel': 1, 'SpellLevel': 1, 'CastingTimeIndex': 1, 'CumulativeAura': 25, 'EffectSpellClassMaskA_2': 64, 'EquippedItemClass': -1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your next Blast Wave deals $s1% increased damage per stack. Consumed by Blast Wave.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Blast Wave damage increased by $s1% per stack.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


ignite_tick_200098 = spell(
    id=200098,
    name='Ignite',
    school=School.FIRE,
    dispel=DispelType.NONE,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, die_sides=0, implicit_target_a=6),
    ],
    spell_icon_id=937,
    notes="Fire Mage rework sec 4.1 - the Ignite accumulator's per-tick payout. Cast by spell_mage_ignite_dot (the script on the visible Ignite aura, 12654) each tick with the bank's share as the custom base point, instead of letting a SPELL_AURA_PERIODIC_DAMAGE tick pay it: this fork applies spell haste to every periodic-damage aura's amplitude (AuraEffect::CalculatePeriodic) and pads the final tick (GetFinalTickBonusMultiplier), both of which would fight an explicit remaining_damage/ticks_remaining bank. AttributesEx2 CANT_CRIT (crits are already priced into the bank, sec 4.1a) + AttributesEx3 ALWAYS_HIT | IGNORE_CASTER_MODIFIERS (the banked damage already went through every caster-side modifier once; SpellDamageBonusTaken still applies so target-side debuffs/Versatility behave like a normal DoT). Carries Ignite's own family bit (SpellClassMask_1 = 0x08000000, same as 12654) so stock Empowered Fire's proc mask still sees it, plus custom dword-2 bit 0x40 so scripts can exclude it by mask.",
    raw_overrides={'AttributesEx2': 536870912, 'AttributesEx3': 537133056, 'AttributesEx5': 8388608, 'BaseLevel': 1, 'SpellLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 3, 'SpellClassMask_1': 134217728, 'SpellClassMask_3': 64, 'SpellPriority': 50, 'SpellVisualID_1': 2638, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Burns the target for $s1 Fire damage.', 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


ignite_12654 = spell(
    id=12654,
    name='Ignite',
    school=School.FIRE,
    dispel=DispelType.MAGIC,
    attributes=8388608,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=4000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=1000),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=937,
    notes="Fire Mage rework sec 4.1 - the visible Ignite aura, now a PERIODIC_DUMMY timing/display vehicle for the server-side bank in MageMechanics (Mage::AddIgniteDamage et al.) instead of a re-applied PERIODIC_DAMAGE DoT. Edits vs stock: tick every 1 sec (was 2; sec 3.3), aura type 3 -> 226 (see ignite_tick_200098 for why), CumulativeAura 255 so the 3.3.5 aura-update packet carries a stack count (it never carries effect amounts) - the script keeps stacks = banked damage / 100, sec 4.1's client-display fallback. Never re-cast while up: a new Fire crit adds to the bank and RefreshDuration()s this aura in place, leaving the tick cadence alone.",
    raw_overrides={'AttributesEx': 136, 'AttributesEx2': 4, 'AttributesEx3': 268697600, 'AttributesEx4': 1048960, 'AttributesEx5': 8388608, 'AttributesEx6': 536870912, 'CastingTimeIndex': 1, 'CumulativeAura': 255, 'ProcChance': 101, 'BaseLevel': 99, 'SpellLevel': 99, 'EquippedItemClass': -1, 'SpellVisualID_1': 2638, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': "Your critical strikes from Fire damage spells cause the target to burn for an additional percentage of your spell's damage over $12654d.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Burning. Each stack is 100 banked Fire damage, paid out evenly over the remaining $t1-sec ticks.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 3, 'SpellClassMask_1': 134217728, 'SpellClassMask_3': 8, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)
scripted_by(ignite_12654, 'spell_mage_ignite_dot')


# ---- Phase 2: new talent-rank spells (200099-200110) ----------------------------------------


lasting_flame_200099 = spell(
    id=200099,
    name='Lasting Flame',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MOD_CUSTOM_STAT_PCT, misc_value=1 << CombatRating.VERSATILITY),
    ],
    spell_icon_id=3175,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (0,1) rank 1: new talent on repurposed stock talent id 27 (Improved Fire Blast). Flat Versatility via this fork's SPELL_AURA_MOD_CUSTOM_STAT_PCT (misc = 1 << CR_VERSATILITY) - level- and gear-independent, never touches PLAYER_FIELD_COMBAT_RATING. Icon 3175 (Molten Core).",
    raw_overrides={'BaseLevel': 1, 'SpellLevel': 1, 'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'NameSubtext_Lang_enUS': 'Rank 1', 'Description_Lang_enUS': 'Increases your Versatility by 1%.'},
)


lasting_flame_200100 = spell(
    id=200100,
    name='Lasting Flame',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MOD_CUSTOM_STAT_PCT, misc_value=1 << CombatRating.VERSATILITY),
    ],
    spell_icon_id=3175,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (0,1) rank 2: new talent on repurposed stock talent id 27 (Improved Fire Blast). Flat Versatility via this fork's SPELL_AURA_MOD_CUSTOM_STAT_PCT (misc = 1 << CR_VERSATILITY) - level- and gear-independent, never touches PLAYER_FIELD_COMBAT_RATING. Icon 3175 (Molten Core).",
    raw_overrides={'BaseLevel': 1, 'SpellLevel': 1, 'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'NameSubtext_Lang_enUS': 'Rank 2', 'Description_Lang_enUS': 'Increases your Versatility by 2%.'},
)


lasting_flame_200101 = spell(
    id=200101,
    name='Lasting Flame',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MOD_CUSTOM_STAT_PCT, misc_value=1 << CombatRating.VERSATILITY),
    ],
    spell_icon_id=3175,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (0,1) rank 3: new talent on repurposed stock talent id 27 (Improved Fire Blast). Flat Versatility via this fork's SPELL_AURA_MOD_CUSTOM_STAT_PCT (misc = 1 << CR_VERSATILITY) - level- and gear-independent, never touches PLAYER_FIELD_COMBAT_RATING. Icon 3175 (Molten Core).",
    raw_overrides={'BaseLevel': 1, 'SpellLevel': 1, 'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'NameSubtext_Lang_enUS': 'Rank 3', 'Description_Lang_enUS': 'Increases your Versatility by 3%.'},
)


burning_soul_200102 = spell(
    id=200102,
    name='Burning Soul',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.NOT_LOSE_CASTING_TIME),
        Effect(type=EffectType.APPLY_AURA, base_points=3, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MOD_SPELL_CRIT_CHANCE),
    ],
    spell_icon_id=11,
    notes='Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (0,3) rank 3: new third rank (stock had 2). Same shape as 11083/12351, same Fire-spell classmask on Effect_1.',
    raw_overrides={'BaseLevel': 1, 'SpellLevel': 1, 'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'NameSubtext_Lang_enUS': 'Rank 3', 'Description_Lang_enUS': 'Increases spell critical strike chance by 3%. Reduces spell pushback suffered from damaging attacks by 100%.', 'EffectSpellClassMaskA_1': 4194325, 'EffectSpellClassMaskA_2': 4096},
)


impact_crater_200103 = spell(
    id=200103,
    name='Impact Crater',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2000, die_sides=0, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.DURATION),
        Effect(type=EffectType.APPLY_AURA, base_points=5, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1137,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (2,1) rank 1: new talent on repurposed stock talent id 30 (Impact). Effect_1 SPELLMOD_DURATION scoped to Meteor (custom dword-2 bit 0x20 -> EffectSpellClassMaskA_3 = 32) lengthens 200096's persistent ground aura; Effect_2 DUMMY = Kindling cap marker (5) read by Phase 3's spell_mage_meteor_impact by icon 1137 (Lava Burst).",
    raw_overrides={'BaseLevel': 1, 'SpellLevel': 1, 'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'NameSubtext_Lang_enUS': 'Rank 1', 'Description_Lang_enUS': 'Your Meteor grants 1 Kindling for each enemy it strikes, up to 5, and its ground burn lasts 2 sec longer.', 'EffectSpellClassMaskA_3': 32},
)


impact_crater_200104 = spell(
    id=200104,
    name='Impact Crater',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4000, die_sides=0, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.DURATION),
        Effect(type=EffectType.APPLY_AURA, base_points=10, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1137,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (2,1) rank 2: new talent on repurposed stock talent id 30 (Impact). Effect_1 SPELLMOD_DURATION scoped to Meteor (custom dword-2 bit 0x20 -> EffectSpellClassMaskA_3 = 32) lengthens 200096's persistent ground aura; Effect_2 DUMMY = Kindling cap marker (10) read by Phase 3's spell_mage_meteor_impact by icon 1137 (Lava Burst).",
    raw_overrides={'BaseLevel': 1, 'SpellLevel': 1, 'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'NameSubtext_Lang_enUS': 'Rank 2', 'Description_Lang_enUS': 'Your Meteor grants 1 Kindling for each enemy it strikes, up to 10, and its ground burn lasts 4 sec longer.', 'EffectSpellClassMaskA_3': 32},
)


tinderbox_200105 = spell(
    id=200105,
    name='Tinderbox',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-5000, die_sides=0, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COOLDOWN),
        Effect(type=EffectType.APPLY_AURA, base_points=10, die_sides=0, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=5, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3170,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (5,0) rank 1: new talent on repurposed stock talent id 2212 (Burning Determination). Effect_1/2 SpellMods scoped to Blast Wave (dword-1 bit 0x40 -> EffectSpellClassMaskA_2 / B_2 = 64; SPELLMOD_COOLDOWN covers Blast Wave's category cooldown too - Player::AddSpellAndCategoryCooldowns applies it to catrec). Effect_3 DUMMY = per-Ignite-tick Kindling chance (5) read by Phase 3's spell_mage_ignite_dot by icon 3170 (Backdraft); the Kindling damage bonus itself is the Kindling aura (200097). Both Blast Wave bonuses multiply.",
    raw_overrides={'BaseLevel': 1, 'SpellLevel': 1, 'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'NameSubtext_Lang_enUS': 'Rank 1', 'Description_Lang_enUS': 'Reduces the cooldown of your Blast Wave by 5 sec and increases its damage by 10%.\n\nEach time your Ignite deals damage, it has a 5% chance to grant Kindling. Your Blast Wave consumes all Kindling, dealing 9% increased damage per stack. Stacks up to 25 times.', 'EffectSpellClassMaskA_2': 64, 'EffectSpellClassMaskB_2': 64},
)


tinderbox_200106 = spell(
    id=200106,
    name='Tinderbox',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-10000, die_sides=0, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COOLDOWN),
        Effect(type=EffectType.APPLY_AURA, base_points=20, die_sides=0, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=10, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3170,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (5,0) rank 2: new talent on repurposed stock talent id 2212 (Burning Determination). Effect_1/2 SpellMods scoped to Blast Wave (dword-1 bit 0x40 -> EffectSpellClassMaskA_2 / B_2 = 64; SPELLMOD_COOLDOWN covers Blast Wave's category cooldown too - Player::AddSpellAndCategoryCooldowns applies it to catrec). Effect_3 DUMMY = per-Ignite-tick Kindling chance (10) read by Phase 3's spell_mage_ignite_dot by icon 3170 (Backdraft); the Kindling damage bonus itself is the Kindling aura (200097). Both Blast Wave bonuses multiply.",
    raw_overrides={'BaseLevel': 1, 'SpellLevel': 1, 'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'NameSubtext_Lang_enUS': 'Rank 2', 'Description_Lang_enUS': 'Reduces the cooldown of your Blast Wave by 10 sec and increases its damage by 20%.\n\nEach time your Ignite deals damage, it has a 10% chance to grant Kindling. Your Blast Wave consumes all Kindling, dealing 9% increased damage per stack. Stacks up to 25 times.', 'EffectSpellClassMaskA_2': 64, 'EffectSpellClassMaskB_2': 64},
)


blazing_speed_200107 = spell(
    id=200107,
    name='Blazing Speed',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MOD_CASTING_SPEED_NOT_STACK),
        Effect(type=EffectType.APPLY_AURA, base_points=3, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MOD_LEECH_PCT),
        Effect(type=EffectType.APPLY_AURA, base_points=1, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2127,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 3 (7,0) rank 3: ProcTypeMask 1114112 = PROC_FLAG_TAKEN_MELEE_AUTO_ATTACK(0x8)|TAKEN_SPELL_MELEE_DMG_CLASS(0x20)|TAKEN_SPELL_RANGED_DMG_CLASS(0x200)|TAKEN_DAMAGE(0x100000) - 'taking direct damage' broadly, filtered further (health <35%, capstone marker present, 30s ICD) by spell_mage_blazing_speed_capstone. EFFECT_2 DUMMY (amount=1) is still the capstone-presence marker read by that same script's icon lookup (2127) - kept so ranks 1-2 (which have no EFFECT_2) can't accidentally proc.",
    raw_overrides={'BaseLevel': 1, 'SpellLevel': 1, 'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'NameSubtext_Lang_enUS': 'Rank 3', 'Description_Lang_enUS': 'Increases your spell haste by 3% and causes your damage to heal you for 3% of the damage dealt.\n\nCapstone Bonus: Taking direct damage while below 35% health dispels all movement impairing effects and increases your movement speed by 50% and your haste by 20% for 6 sec. While active, you can cast non-channeled Fire spells while moving. This effect can only occur every 30 sec.', 'ProcTypeMask': 1114112},
)


fanned_flames_200108 = spell(
    id=200108,
    name='Fanned Flames',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3173,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (7,1) rank 1: new talent on repurposed stock talent id 24 (Molten Shields). EFFECT_0 DUMMY = proc chance marker (15) for Phase 3's Living Bomb tick script (2.5 sec ICD, per tick per target) by icon 3173 (Fire and Brimstone). Everything else (the instant/+100% Scorch buff, the non-crit Ignite banking) is Phase 3.",
    raw_overrides={'BaseLevel': 1, 'SpellLevel': 1, 'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'NameSubtext_Lang_enUS': 'Rank 1', 'Description_Lang_enUS': 'Your Living Bomb periodic damage has a 15% chance to make your next Scorch instant cast and deal 100% increased damage. This Scorch adds 100% of its damage to your Ignite even if it does not critically strike.'},
)


fanned_flames_200109 = spell(
    id=200109,
    name='Fanned Flames',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=10, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3173,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (7,1) rank 2: new talent on repurposed stock talent id 24 (Molten Shields). EFFECT_0 DUMMY = proc chance marker (30) for Phase 3's Living Bomb tick script (2.5 sec ICD, per tick per target) by icon 3173 (Fire and Brimstone). Everything else (the instant/+100% Scorch buff, the non-crit Ignite banking) is Phase 3.",
    raw_overrides={'BaseLevel': 1, 'SpellLevel': 1, 'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'NameSubtext_Lang_enUS': 'Rank 2', 'Description_Lang_enUS': 'Your Living Bomb periodic damage has a 30% chance to make your next Scorch instant cast and deal 100% increased damage. This Scorch adds 100% of its damage to your Ignite even if it does not critically strike.'},
)


fanned_flames_200110 = spell(
    id=200110,
    name='Fanned Flames',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=15, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3173,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (7,1) rank 3: new talent on repurposed stock talent id 24 (Molten Shields). EFFECT_0 DUMMY = proc chance marker (45) for Phase 3's Living Bomb tick script (2.5 sec ICD, per tick per target) by icon 3173 (Fire and Brimstone). Everything else (the instant/+100% Scorch buff, the non-crit Ignite banking) is Phase 3.",
    raw_overrides={'BaseLevel': 1, 'SpellLevel': 1, 'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'NameSubtext_Lang_enUS': 'Rank 3', 'Description_Lang_enUS': 'Your Living Bomb periodic damage has a 45% chance to make your next Scorch instant cast and deal 100% increased damage. This Scorch adds 100% of its damage to your Ignite even if it does not critically strike.'},
)


firestarter_54741 = spell(
    id=54741,
    name='Firestarter',
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.CASTING_TIME),
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COST),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=3262,
    notes='Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (8,0) capstone buff: stock instant + free, plus a new +30% SPELLMOD_DAMAGE (direct only - the DoT half is SPELLMOD_DOT) on Effect_3, scoped to Flamestrike (EffectSpellClassMaskC_1 = 4). Consumed by the Flamestrike cast as before.',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 4, 'EffectSpellClassMaskB_1': 4, 'SpellVisualID_1': 12021, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': "Your damaging Blast Wave, Dragon's Breath and Meteor spells make your next Flamestrike spell instant cast, cost no mana, and deal 30% more direct damage.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next Flamestrike spell is instant cast, costs no mana and deals 30% more direct damage.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 3, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskC_1': 4},
)


# ---- Phase 3: hidden buffs/markers for the C++ talent scripts (200112-200119) ---------------

flame_throwing_lockout_200112 = spell(
    id=200112,
    name='Flame Throwing',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=136,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 3 (2,0) capstone - hidden 12s lockout marker (spec: 'inactive for 12 sec after use', consumed by a Fireball that actually benefited - user call 2026-09-15). Pure presence-check by spell_mage_flame_throwing_capstone/spell_mage_fireball; no real gameplay effect of its own. Icon 136 = Flame Throwing's own.",
    raw_overrides={'AttributesEx': 128, 'CastingTimeIndex': 1, 'ProcChance': 101, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Recharging', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': '', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Fireball cast time reduction is recharging.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


blazing_speed_escape_200113 = spell(
    id=200113,
    name='Blazing Speed',
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=50, implicit_target_a=1, apply_aura=AuraType.MOD_INCREASE_SPEED),
        Effect(type=EffectType.APPLY_AURA, base_points=20, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MOD_CASTING_SPEED_NOT_STACK),
    ],
    spell_icon_id=2127,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 3 (7,0) capstone escape - 6s +50% move speed / +20% spell haste. The 'cast non-channeled Fire spells while moving' clause is Mage::CanCastWhileMoving (Spell.cpp hook, checks HasAura(this)), not DBC-expressible. Movement-impair dispel (RemoveMovementImpairingAuras) and the 30s ICD (200114) are applied by the triggering script, not this aura itself. No `attributes=464`/DO_NOT_DISPLAY - real player-facing buff, must show in the aura bar (same invisible-buff bug as Fanned Flames 200118, found via playtest 2026-09-16 and fixed here too). `EquippedItemClass: -1` is required here too (found via the Fanned Flames follow-up bug, playtest 2026-09-17): the DSL/DBC default is 0 (ITEM_CLASS_CONSUMABLE, not 'no requirement'), and once a spell is non-passive Spell::CheckCast actually runs CheckItems() against it - an unhandled EquippedItemClass in Player::HasItemFitToSpellRequirements's switch falls through to a hard false, so the cast fails SPELL_FAILED_EQUIPPED_ITEM_CLASS outright. The passive marker/ICD spells in this file never hit this because passive spells skip CheckItems() entirely (Spell.cpp).",
    raw_overrides={'AttributesEx': 128, 'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'ProcChance': 101, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': '', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement speed and spell haste increased. Can cast non-channeled Fire spells while moving.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


blazing_speed_escape_icd_200114 = spell(
    id=200114,
    name='Blazing Speed',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2127,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 3 (7,0) capstone - hidden 30s internal-cooldown marker ('This effect can only occur every 30 sec'). Applied alongside 200113, outlives it (30s > 6s) so its own presence is the gate.",
    raw_overrides={'AttributesEx': 128, 'CastingTimeIndex': 1, 'ProcChance': 101, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Recharging', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': '', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Blazing Speed is recharging.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


burnout_damage_buff_200115 = spell(
    id=200115,
    name='Burnout',
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=6, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=127),
    ],
    spell_icon_id=2998,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 3 (6,0) capstone - 'Dealing direct Fire damage to targets afflicted by your Ignite increases your spell damage by 6% for 8 sec.' MOD_DAMAGE_PERCENT_DONE (misc 127 = every school) is a native aura the engine already reads generically - no read-side script needed, only the grant (spell_mage_burnout). Refreshes on each qualifying hit rather than stacking (CumulativeAura unset). No `attributes=464`/DO_NOT_DISPLAY - real player-facing buff, must show in the aura bar (same invisible-buff bug as Fanned Flames 200118, found via playtest 2026-09-16 and fixed here too). `EquippedItemClass: -1` is required here too - see Blazing Speed's (200113) note for the full mechanism.",
    raw_overrides={'AttributesEx': 128, 'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'ProcChance': 101, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': '', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Spell damage increased by 6%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


burnout_explosion_200116 = spell(
    id=200116,
    name='Burnout',
    school=School.FIRE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    range_yards=50000.0,
    radius_yards=8.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=53, implicit_target_b=16, radius_yards=8.0),
    ],
    spell_icon_id=2998,
    notes="Fire Mage rework Phase 3 (6,0) capstone - 'Dealing direct magic non-Fire damage to targets affected by your Ignite causes an explosion.' User call 2026-09-15: 50% of the target's remaining Ignite bank (Mage::GetIgniteRemaining), bank NOT consumed. CANT_CRIT + IGNORE_CASTER_MODIFIERS + ALWAYS_HIT, same reasoning as Flashpoint (200119)/the Ignite tick vehicle (200098): the bank already prices in crit rate/damage once, letting the explosion crit (and feed Ignite again) would double it. Target-centered AoE (A=53 TARGET_DEST_TARGET_ENEMY, B=16 TARGET_UNIT_DEST_AREA_ENEMY), same pair as Living Bomb's own explosion (44461). 6 sec ICD is the caster-side marker 200117, not on this spell.",
    raw_overrides={'BaseLevel': 1, 'SpellLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'InterruptFlags': 0, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Explodes for Fire damage.', 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'AttributesEx2': 536870912, 'AttributesEx3': 537133056},
)
bonus_coefficients(burnout_explosion_200116, direct=0.0, comment='Mage - Burnout explosion (fire-mage-rework.md sec 6, Burnout capstone): flat % of the Ignite bank, no independent SP scaling')


burnout_explosion_icd_200117 = spell(
    id=200117,
    name='Burnout',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2998,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 3 (6,0) capstone - hidden 6s ICD marker for the Ignite explosion (user call 2026-09-15).",
    raw_overrides={'AttributesEx': 128, 'CastingTimeIndex': 1, 'ProcChance': 101, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Recharging', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': '', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Ignite Explosion is recharging.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


fanned_flames_ready_200118 = spell(
    id=200118,
    name='Fanned Flames',
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.CASTING_TIME),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=3173,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 3 (7,1) - 'next Scorch instant cast and deal 100% increased damage.' Same non-charge-consumption shape as the stock Firestarter buff (54741, ProcCharges=0) - explicitly removed by spell_mage_scorch's AfterCast, not the engine's charge system, matching this codebase's existing precedent (spell_mage_missile_barrage_proc is consumed by spell_mage_arcane_missiles the same way). Both effects scoped to Scorch alone (EffectSpellClassMaskA_1/B_1 = 16). 15s safety-net duration so it can't linger forever if the mage never casts Scorch (spec gives no expiry; a persistent 45/45%-uptime buff with no cap would be a bug, not a feature). No `attributes=464`/DO_NOT_DISPLAY here (unlike the hidden ICD/DUMMY markers elsewhere in this file) - this is a real player-facing buff that must show in the aura bar so the player knows to use their empowered Scorch (bug found via playtest 2026-09-16: the buff was applying mechanically but invisibly). Second bug found via playtest 2026-09-17, same root cause: `EquippedItemClass` was never overridden, so it defaulted to 0 (ITEM_CLASS_CONSUMABLE). That's harmless on a passive spell (Spell::CheckCast skips CheckItems() for passive spells entirely) but once this spell went non-passive to fix the display bug above, every cast started failing SPELL_FAILED_EQUIPPED_ITEM_CLASS (an unhandled case in Player::HasItemFitToSpellRequirements's switch falls through to false) - confirmed live via debug logging (icdResult=255 passive-ICD-marker success vs readyResult=29 this spell's failure, same tick). `EquippedItemClass: -1` (matching every other real spell in this codebase) is required on any spell that's both non-passive and player-self-cast.",
    raw_overrides={'AttributesEx': 128, 'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'ProcChance': 101, 'EffectSpellClassMaskA_1': 16, 'EffectSpellClassMaskB_1': 16, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': '', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Next Scorch is instant cast and deals 100% increased damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


# ---- Phase 3: spell_script_names bindings for the new/modified scripts below ---------------
scripted_by(flame_throwing_12353, 'spell_mage_flame_throwing_capstone')
scripted_by(-burnout_44449.id, 'spell_mage_burnout_capstone')
scripted_by(-playing_with_fire_31638.id, 'spell_mage_playing_with_fire')
scripted_by(blazing_speed_200107, 'spell_mage_blazing_speed_capstone')
scripted_by(meteor_impact_200096, 'spell_mage_meteor_impact')


# Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 3 - Hot Streak's own spell_proc row corrected: stock data's dword-1 mask (0x11000) has the
# right Frostfire Bolt bit (0x1000) but the wrong second bit (0x10000, not Living Bomb's real
# 0x20000) - explicitly re-declared here with the exact 5 trigger spells sec 8.2/6 names
# (Fireball/Fire Blast/Scorch/Living Bomb/Frostfire Bolt), Pyroblast excluded by construction
# (its own family bit, 0x400000, is in neither mask - see (2,2)'s implementation note).
# HitMask left at 0 (no crit-only filter here) - spell_mage_hot_streak's own
# eventInfo.GetHitMask() & PROC_EX_CRITICAL_HIT check is what enforces "2 non-periodic criticals",
# same as the pre-existing stock row.
procs_on(-44445, proc_flags=0, school_mask=0, family_name=3,
         family_mask=(19, 135168, 0),  # dword0: Fireball(1)|Fire Blast(2)|Scorch(16); dword1: Living Bomb(131072)|Frostfire Bolt(4096)
         spell_type_mask=1, spell_phase_mask=2, hit_mask=0, chance=0)


fanned_flames_icd_200120 = spell(
    id=200120,
    name='Fanned Flames',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    duration_ms=2500,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3173,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 3 (7,1) - hidden 2.5s ICD marker for the Living Bomb tick roll (sec 6 (7,1): 'deliberately below Living Bomb's 3 sec tick interval'). Same HasAura idiom as Netherwind Presence's own ICD marker (200091).",
    raw_overrides={'AttributesEx': 128, 'CastingTimeIndex': 1, 'ProcChance': 101, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Recharging', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': '', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Fanned Flames is recharging.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)

scripted_by(flame_throwing_lockout_200112, 'spell_mage_flame_throwing_lockout')


# ---- Fire Mage rework: Scorched Earth (1,1) and Stoking the Fire (9,1), 2026-09-16 tree review --

scorched_earth_200121 = spell(
    id=200121,
    name='Scorched Earth',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3063,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (1,1) rank 1: new talent, 2 ranks. Effect_0/1 are plain SpellMods (+15% Flamestrike direct/DoT damage, both halves per user call 2026-09-16), scoped via classmask to Flamestrike alone (EffectSpellClassMaskA_1/EffectSpellClassMaskB_1 = 4, Flamestrike's own SpellClassMask_1). Effect_2 is a DUMMY marker (5) carrying the vulnerability-debuff percentage read by spell_mage_flamestrike_vulnerability via the marker-aura-by-icon idiom - icon 3063 (talent-tooltip-audit, 2026-09-17: was 1899, swapped to Spell_Shaman_StormEarthFire, still unique within the Fire tab) - keep spell_mage.cpp's MAGE_ICON_SCORCHED_EARTH in sync with this value.",
    raw_overrides={'BaseLevel': 1, 'SpellLevel': 1, 'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': 4, 'EffectSpellClassMaskB_1': 4, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Flamestrike by 15%. Enemies standing in your Flamestrike take 5% increased damage from your Fire spells.', 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


scorched_earth_200122 = spell(
    id=200122,
    name='Scorched Earth',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=30, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=30, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
        Effect(type=EffectType.APPLY_AURA, base_points=10, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3063,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (1,1) rank 2: 2 ranks total (design doc originally listed 3 ranks but only ever gave 2 tooltip values - user call 2026-09-16: it's a 2-rank talent).",
    raw_overrides={'BaseLevel': 1, 'SpellLevel': 1, 'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': 4, 'EffectSpellClassMaskB_1': 4, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Flamestrike by 30%. Enemies standing in your Flamestrike take 10% increased damage from your Fire spells.', 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


scorched_earth_vulnerability_200123 = spell(
    id=200123,
    name='Scorched Earth',
    school=School.FIRE,
    dispel=DispelType.MAGIC,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=6, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=int(School.FIRE)),
    ],
    spell_icon_id=37,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2/3 (1,1) - the debuff half of Scorched Earth, applied by spell_mage_flamestrike_vulnerability to any target Flamestrike's own persistent-area aura (2120 effect 1) lands on, via CastCustomSpell(SPELLVALUE_BASE_POINT0, <marker value>, ...) - base_points is a placeholder (0), the real 5/10% comes from the rank marker DUMMY on 200121/200122 at cast time. 8 sec duration matches Flamestrike's own zone duration; re-entering the zone (a fresh persistent-area apply) refreshes it. Icon reused from Flamestrike (37) since this is purely an internal companion debuff, never seen as its own Spellbook entry.",
    raw_overrides={'AttributesEx3': 268566528, 'BaseLevel': 1, 'SpellLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'PreventionType': 1, 'ProcChance': 101, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Standing in Scorched Earth. Fire damage taken increased.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)
scripted_by(2120, 'spell_mage_flamestrike_vulnerability')  # Flamestrike - flamestrike_2120 itself lives in mage_spells.py, avoid a circular import for one id


stoking_the_fire_buff_200127 = spell(
    id=200127,
    name='Stoking the Fire',
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
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=2064,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (9,1) rank 1's stacking self-buff - max 3 stacks (CumulativeAura), +1% Fire spell damage per stack (same classmask scoping as Fire Power (5,2): EffectSpellClassMaskA_1/A_2, EffectSpellClassMaskB_1/B_2, copied verbatim from fire_power_12378 so 'Fire spell' means the same set of spells everywhere in this tree). 5 sec duration, refreshed (not stacked-and-extended) by every subsequent cast while stacking. **attributes=0, not 464** - root-caused 2026-09-16: SpellInfo::IsMultiSlotAura() returns true for any SPELL_ATTR0_PASSIVE spell, and Unit::_TryStackingOrRefreshingExistingAura's entire stack-refresh path (GetOwnedAura lookup -> ModStackAmount) is skipped for multi-slot auras - every re-cast created a brand-new instance instead of incrementing the existing one, observed live as remove-then-reapply at stack 1 in the sim report's raw auraEvents, never climbing. attributes=464 (this rework's usual talent-rank-marker boilerplate) sets SPELL_ATTR0_PASSIVE (0x40); this spell isn't a talent-rank marker, it's a repeatedly-CastSpell'd stacking buff, so it needs the same attributes=0 Kindling's own buff (200097) already uses for exactly this reason.",
    raw_overrides={'AttributesEx': 128, 'CumulativeAura': 3, 'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': 12845079, 'EffectSpellClassMaskA_2': 69704, 'EffectSpellClassMaskB_1': 4194309, 'EffectSpellClassMaskB_2': 135168, 'EffectBonusMultiplier_2': 1.0, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Fire damage increased by $s1% per stack.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


stoking_the_fire_buff_200128 = spell(
    id=200128,
    name='Stoking the Fire',
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
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=2064,
    notes='Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (9,1) rank 2 buff - identical to 200127 except CumulativeAura 6 (rank 2 cap).',
    raw_overrides={'AttributesEx': 128, 'CumulativeAura': 6, 'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': 12845079, 'EffectSpellClassMaskA_2': 69704, 'EffectSpellClassMaskB_1': 4194309, 'EffectSpellClassMaskB_2': 135168, 'EffectBonusMultiplier_2': 1.0, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Fire damage increased by $s1% per stack.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


stoking_the_fire_buff_200129 = spell(
    id=200129,
    name='Stoking the Fire',
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
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
    ],
    spell_icon_id=2064,
    notes='Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (9,1) rank 3 buff - identical to 200127 except CumulativeAura 9 (rank 3 cap).',
    raw_overrides={'AttributesEx': 128, 'CumulativeAura': 9, 'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellPriority': 50, 'EffectSpellClassMaskA_1': 12845079, 'EffectSpellClassMaskA_2': 69704, 'EffectSpellClassMaskB_1': 4194309, 'EffectSpellClassMaskB_2': 135168, 'EffectBonusMultiplier_2': 1.0, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'AuraDescription_Lang_enUS': 'Fire damage increased by $s1% per stack.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


stoking_the_fire_200124 = spell(
    id=200124,
    name='Stoking the Fire',
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
    ],
    spell_icon_id=1923,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (9,1) rank 1 - passive marker; procs_on (below) fires this on every successful Fire-school damaging cast. EFFECT_0 DUMMY, not PROC_TRIGGER_SPELL: an earlier pass used the native auto-cast (like stock Improved Scorch's 22959), but live testing (2026-09-16) showed AuraEffect::HandleProcTriggerSpellAuraProc's triggered CastSpell doesn't refresh-and-stack an existing CumulativeAura the way an explicit CastSpell does - every proc showed as remove-then-reapply at stack 1 in the sim report's raw auraEvents, never climbing past 1. spell_mage_stoking_the_fire (Phase 3) now does the CastSpell explicitly from OnEffectProc, the same proven-stacking shape as Kindling's Mage::GrantKindling(). Triggers rank 1's buff (200127, cap 3).",
    raw_overrides={'BaseLevel': 1, 'SpellLevel': 1, 'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Each Fire spell you cast increases your Fire damage by 1%, stacking up to 3 times. Resets when you have not dealt Fire damage for 5 sec.', 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)
procs_on(stoking_the_fire_200124, proc_flags=65536, school_mask=4, spell_type_mask=1, spell_phase_mask=1, chance=100.0)


stoking_the_fire_200125 = spell(
    id=200125,
    name='Stoking the Fire',
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
    ],
    spell_icon_id=1923,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (9,1) rank 2 - see rank 1's (200124) note for why this is DUMMY + spell_mage_stoking_the_fire, not a native PROC_TRIGGER_SPELL. Triggers rank 2's buff (200128, cap 6).",
    raw_overrides={'BaseLevel': 1, 'SpellLevel': 1, 'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Each Fire spell you cast increases your Fire damage by 1%, stacking up to 6 times. Resets when you have not dealt Fire damage for 5 sec.', 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)
procs_on(stoking_the_fire_200125, proc_flags=65536, school_mask=4, spell_type_mask=1, spell_phase_mask=1, chance=100.0)


stoking_the_fire_200126 = spell(
    id=200126,
    name='Stoking the Fire',
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
    ],
    spell_icon_id=1923,
    notes="Fire Mage rework (docs/reworks/fire-mage-rework.md) Phase 2 (9,1) rank 3 - see rank 1's (200124) note for why this is DUMMY + spell_mage_stoking_the_fire, not a native PROC_TRIGGER_SPELL. Triggers rank 3's buff (200129, cap 9).",
    raw_overrides={'BaseLevel': 1, 'SpellLevel': 1, 'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 3, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Each Fire spell you cast increases your Fire damage by 1%, stacking up to 9 times. Resets when you have not dealt Fire damage for 5 sec.', 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)
procs_on(stoking_the_fire_200126, proc_flags=65536, school_mask=4, spell_type_mask=1, spell_phase_mask=1, chance=100.0)
scripted_by(stoking_the_fire_200124, 'spell_mage_stoking_the_fire')
scripted_by(stoking_the_fire_200125, 'spell_mage_stoking_the_fire')
scripted_by(stoking_the_fire_200126, 'spell_mage_stoking_the_fire')
