"""
Rogue - spells that are never directly cast - proc/periodic-tick effects, trigger_spell targets, hidden talent-rank buffs, etc..

Split from a single source/classes/rogue.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .rogue_...` below) resolve.
"""

from lib.dsl import AuraType, DispelType, Effect, EffectType, PowerType, School
from lib.dsl.registry import leave_spell_group, pot_text, procs_on, remove_spell_proc, scripted_by, spell, unbind_script

from . import _masks as m
from .rogue_combat import (HACK_AND_SLASH_CHANCE_PCT, PREY_CRIT_HEALTH_PCT, PREY_DAMAGE_HEALTH_PCT,
                           SURPRISE_ATTACKS_EXTRA_SHOTS, UNFAIR_ADVANTAGE_ICD_MS, _c, _sec)
from .rogue_subtlety import (CHEAT_DEATH_CAP_MAX_HEALTH_PCT, SINISTER_CALLING_MAX_TARGETS, SINISTER_CALLING_PCT_PER_CP,
                             SLAUGHTER_CDR_MS, THROWING_SPEC_EXTRA_TARGETS, sinister_calling_volley_204165)


def _read_mask(effect_no, mask):
    """The raw EffectSpellClassMask<letter>_<dword> keys for one of `_masks`' (d0, d1, d2) reader composites: the letter
    is the effect (A = effect 1, B = 2, C = 3), the number the dword (1 = d0, 2 = d1, 3 = d2; dbcfmt.py, bug doc
    "wrong dword"). Zero dwords are left out, so the DBC column stays 0. Used for the S1 reader masks below."""
    return {f'EffectSpellClassMask{"ABC"[effect_no - 1]}_{dword}': value
            for dword, value in enumerate(mask, start=1) if value}


def _grey(text):
    """The capstone sentence on a rank below the last (paladin / hunter / DK / S1 rank-text convention)."""
    return f'|cFF9D9D9D{text}|r'


def _with_cap(text, capstone, last):
    """`text` plus the capstone sentence: plain on the last rank, grey below it."""
    return f'{text} {capstone if last else _grey(capstone)}'


def _sinister_calling_text(last):
    """Sinister Calling's rank tooltip; the volley's damage is quoted from 204165 itself (pot_text), so a retune of its
    potency updates this text too."""
    return _with_cap(
        'Increases your total Agility by $s1%.',
        'Capstone: Your finishing moves have a ' + _c(SINISTER_CALLING_PCT_PER_CP) + '% chance per combo point spent '
        'to fling a volley of knives at the target and up to ' + str(int(SINISTER_CALLING_MAX_TARGETS['value']) - 1)
        + ' other nearby enemies, dealing ' + pot_text(sinister_calling_volley_204165)
        + ' Shadowstrike damage to each.', last)


pick_pocket_921 = spell(
    id=921,
    name='Pick Pocket',
    school=School.NORMAL,
    attributes=196624,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=71, base_points=-1, implicit_target_a=6),
    ],
    spell_icon_id=227,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 2232352, 'AttributesEx3': 196608, 'AttributesEx4': 8388608, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 4, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Pick the target's pocket.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 2, 'ShapeshiftMask': 536870912, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 8, 'SpellLevel': 4, 'SpellVisualID_1': 251},
)


safe_fall_1860 = spell(
    id=1860,
    name='Safe Fall',
    school=School.NORMAL,
    attributes=262224,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=16, implicit_target_a=1, apply_aura=144),
    ],
    spell_icon_id=1658,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 40, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces damage from falling.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Passive', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 32768, 'SpellClassSet': 8, 'SpellLevel': 40},
)


deadly_poison_2818 = spell(
    id=2818,
    name='Deadly Poison',
    school=School.NATURE,
    dispel=DispelType.POISON,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000, ap_potency=4.5, potency_kind='periodic'),
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=197),
    ],
    spell_icon_id=513,
    notes=(
        'single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 30); RealPointsPerLevel from rank1→level-60 slope (anchor 25349, rank 5); coefficient/cast_time_ms/mana_cost_pct from max rank (57970, rank 9); flat energy cost kept as-is (Rogue is Energy-based, not Mana). '
        'potency-system (PLAN P7-Rogue): converted to ap_potency=4.5 (periodic, matching the live, '
        'already-mismatched ap_dot_bonus=0.030 coefficient\'s base-implied potency from '
        'rogue-potency-report.md/rogue-potency-proposals.txt) - reproduces the pre-conversion V60 '
        'of 24 exactly (simulate_value).'
    ),
    raw_overrides={'AttributesEx': 131208, 'AttributesEx2': 16777220, 'AttributesEx3': 128, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Taking Nature damage over time.', 'CastingTimeIndex': 1, 'CumulativeAura': 5, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Poisons the target for {pot1.total} Nature damage over $2818d. Stacks up to 5 times.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassMask_1': m.DEADLY_POISON, 'SpellClassMask_2': m.POISON_GROUP, 'SpellClassSet': 8, 'SpellLevel': 30, 'SpellVisualID_1': 5100},
)


mutilate_5374 = spell(
    id=5374,
    name='Mutilate',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=121, base_points=43, points_per_level=2.3220338983050848, implicit_target_a=6),
    ],
    spell_icon_id=533,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1→level-60 slope (anchor 48665, rank 6); coefficient/cast_time_ms/mana_cost_pct from max rank (48665, rank 6); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)',
    raw_overrides={'AttributesEx3': 1536, 'AttributesEx4': 1, 'AttributesEx7': 58720256, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly attacks with both weapons for $<percent>% weapon damage plus additional $5374s1 with each weapon.  Damage is increased by 20% against Poisoned targets.  Awards 2 combo points.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 32768, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 2, 'SpellClassSet': 8, 'SpellDescriptionVariableID': 172, 'SpellLevel': 1},
)


instant_poison_8680 = spell(
    id=8680,
    name='Instant Poison',
    school=School.NATURE,
    dispel=DispelType.POISON,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=30, potency_kind='direct', time_basis_ms=1500, implicit_target_a=6),
    ],
    spell_icon_id=247,
    notes=(
        'single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1→level-60 slope (anchor 11337, rank 6); coefficient/cast_time_ms/mana_cost_pct from max rank (57965, rank 9); flat energy cost kept as-is (Rogue is Energy-based, not Mana). '
        'potency-system (PLAN P7-Rogue): converted to ap_potency=29.2 (direct). '
        'rogue-rework RG0a: ap_potency 30 direct, time_basis_ms 1500 ("a payout at 1.5 sec", rogue-shared-rework.md '
        'Instant Poison); SpellClassMask_2 gains the poison group bit (d1 b19); range 100 and EquippedItemClass -1 '
        'kept (script-cast payload of the 203701 self aura).'
    ),
    raw_overrides={'AttributesEx': 136, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Deals {pot1} Nature damage to the target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassMask_1': m.INSTANT_POISON, 'SpellClassMask_2': m.POISON_GROUP, 'SpellClassSet': 8, 'SpellLevel': 20, 'SpellVisualID_1': 5100},
)


vanish_11327 = spell(
    id=11327,
    name='Vanish',
    school=School.NORMAL,
    dispel=DispelType.STEALTH,
    attributes=169148688,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=169, points_per_level=5.0, implicit_target_a=1, apply_aura=16),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MOD_INCREASE_SPEED),
    ],
    spell_icon_id=252,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 22); RealPointsPerLevel from rank1→level-60 slope (anchor 11329, rank 2); coefficient/cast_time_ms/mana_cost_pct from max rank (26888, rank 3); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)',
    raw_overrides={'ActiveIconID': 30, 'AttributesEx': 32, 'AttributesEx2': 2, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Improved stealth.', 'AuraInterruptFlags': 15364, 'BaseLevel': 22, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712188, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ExcludeCasterAuraState': 12, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'ShapeshiftMask': 536870912, 'SpellClassMask_1': 2048, 'SpellClassSet': 8, 'SpellLevel': 22, 'SpellVisualID_1': 255},
)


wound_poison_13218 = spell(
    id=13218,
    name='Wound Poison',
    school=School.NATURE,
    dispel=DispelType.POISON,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=6, apply_aura=271),
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=10, potency_kind='direct', time_basis_ms=1500, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=197),
    ],
    spell_icon_id=1496,
    notes=(
        'single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 32); RealPointsPerLevel from rank1→level-60 slope (anchor 13224, rank 4); coefficient/cast_time_ms/mana_cost_pct from max rank (57975, rank 7); flat energy cost kept as-is (Rogue is Energy-based, not Mana). '
        'potency-system (PLAN P7-Rogue): effect2 (the damage effect) converted to ap_potency (direct). '
        'rogue-rework RG0a: effect1 is no longer the healing reduction (aura 118) but aura 271 '
        'MOD_DAMAGE_FROM_CASTER stored 19 (+20%) on the enemy, read by caster guid + class mask '
        '(EffectSpellClassMaskA_1 = Rupture d0 b20 | Garrote d0 b8), so only this rogue\'s bleeds take '
        'the bonus; effect2 ap_potency 10 direct, time_basis_ms 1500 (the potency row stays on effect_index '
        '1); effect3 aura 197 untouched; range 100 (the RangeIndex 2 / 5 yd raw key is gone: a script-cast '
        'payload is range-checked even when triggered, handoff C4); SpellClassMask_2 keeps d1 b19. '
        'rogue-rework S2a A2: the aura-271 reader mask is now WOUND_BLEED_READ_S2 (S1\'s + Hemorrhage d2 b12: the bleed 204160 and its tick 204161). '
        'rogue-rework S1a A2: the aura-271 reader mask is now WOUND_BLEED_READ_S1 (Rupture + Garrote d0, Doomblade d2 b11: '
        'the Doomblade bleed 203829 and its tick 203830 take the bonus); spell_rog_wound_poison_mastery adds Mastery / 2 '
        'to eff0 when the caster holds the Improved Poisons capstone 14115.'
    ),
    raw_overrides={'AttributesEx': 136, 'AttributesEx2': 16777216, 'AttributesEx3': 131200, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': "Taking more damage from the rogue's bleeds.", 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Deals {pot2} Nature damage and wounds the target for $13218d, causing the rogue's bleeds to deal $13218s1% more damage to it.", **m.read_mask_keys(0, m.WOUND_BLEED_READ_S2), 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 32768, 'SpellClassMask_1': m.WOUND_POISON, 'SpellClassMask_2': m.POISON_GROUP, 'SpellClassSet': 8, 'SpellLevel': 32, 'SpellVisualID_1': 5100},
)


remorseless_14143 = spell(
    id=14143,
    name='Remorseless',
    school=School.NORMAL,
    attributes=134217728,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, points_per_level=0.3333333333333333, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=695,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1→level-60 slope (anchor 14149, rank 2); coefficient/cast_time_ms/mana_cost_pct from max rank (14149, rank 2); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Critical strike chance for your next Sinister Strike, Backstab, Mutilate, Ambush, Hemorrhage, or Ghostly strike increased by $s1%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'After killing an opponent that yields experience or honor, gives you a $14143s1% increased critical strike chance on your next Sinister Strike, Hemorrhage, Backstab, Mutilate, Ambush, or Ghostly Strike.  Lasts $14143d.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 100663814, 'EffectSpellClassMaskA_2': 6, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 8},
)


anesthetic_poison_26688 = spell(
    id=26688,
    name='Anesthetic Poison',
    school=School.NATURE,
    dispel=DispelType.POISON,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=10, potency_kind='direct', time_basis_ms=1500, implicit_target_a=6),
        Effect(type=EffectType.DISPEL, implicit_target_a=6, misc_value=9),
    ],
    spell_icon_id=110,
    notes=(
        'rogue-rework RG0a: ap_potency 10 direct, time_basis_ms 1500 (was base_potency 57.2 at SpellLevel 68; '
        'attack-power potency like every rogue effect); SpellLevel 40 (learn level, was 68); SpellClassMask_2 '
        'gains the poison group bit (d1 b19) next to the identity bit d1 b4; DISPEL misc 9 (Enrage) kept; range '
        '100 and EquippedItemClass -1 kept (script-cast payload of the 203706 self aura); spell_threat row '
        'untouched.'
    ),
    raw_overrides={'AttributesEx': 1160, 'AttributesEx2': 16777216, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Deals {pot1} Nature damage to the target and removes $26688s2 Enrage effect from it.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassMask_2': m.ANESTHETIC_POISON | m.POISON_GROUP, 'SpellClassSet': 8, 'SpellLevel': 40, 'SpellVisualID_1': 5100},
)


mutilate_27576 = spell(
    id=27576,
    name='Mutilate',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=121, base_points=43, points_per_level=2.3220338983050848, implicit_target_a=6),
    ],
    spell_icon_id=533,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1→level-60 slope (anchor 48664, rank 6); coefficient/cast_time_ms/mana_cost_pct from max rank (48664, rank 6); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)',
    raw_overrides={'AttributesEx3': 16777728, 'AttributesEx7': 58720256, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly attacks with both weapons for $<percent>% weapon damage plus additional $5374s1 with each weapon.  Damage is increased by 20% against Poisoned targets.  Awards 2 combo points.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 32768, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 4, 'SpellClassSet': 8, 'SpellDescriptionVariableID': 172, 'SpellLevel': 1},
)


infectious_poisons_51630 = spell(
    id=51630,
    name='Infectious Poisons',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, points_per_level=0.8333333333333334, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=18),
        Effect(type=EffectType.APPLY_AURA, base_points=9, points_per_level=0.16666666666666666, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=2956,
    notes='single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1→level-60 slope (anchor 51631, rank 2); coefficient/cast_time_ms/mana_cost_pct from max rank (51631, rank 2); MaxLevel set to 80; flat energy cost kept as-is (Rogue is Energy-based, not Mana)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage caused by your Instant Poison and Deadly Poison by $s2%.  In addition, when a target you've poisoned is healed or cured, there is a $h% chance the poison afflicts the healer.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 131072, 'EffectSpellClassMaskB_1': 73728, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellVisualID_1': 11838},
)


throwing_specialization_5952 = spell(
    id=5952,
    name='Throwing Specialization',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER),
    ],
    spell_icon_id=2910,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Throwing Specialization": eff0 pct DAMAGE +10 on THROWING_SPEC_READ '
        '(Deadly Throw d1 b0, Fan of Knives d1 b18: 51723, 52874, the Second Volley copies and the Deadly Throw copy '
        '204168); the stock RANGE modifier and the interrupt proc (51680) are gone, raw ProcTypeMask 0 / ProcChance '
        '101 with the -5952 / 32748 spell_proc rows removed below. The capstone (51679 held) is read by '
        "spell_rog_deadly_throw_subtlety. The copy 204168 carries d1 b0 only, so an Assassination hybrid's "
        'Ruthlessness / Find Weakness on finishers do not reach the copies (R21).'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': _with_cap('Increases the damage of your Deadly Throw and Fan of Knives by $s1%.', f'Capstone: Your Deadly Throw also strikes up to {_c(THROWING_SPEC_EXTRA_TARGETS)} additional enemies near the target.', False),
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'ProcTypeMask': 0,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **m.read_mask_keys(0, m.THROWING_SPEC_READ),
        **m.clear_mask_keys(1),
    },
)


dual_wield_specialization_13715 = spell(
    id=13715,
    name='Dual Wield Specialization',
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
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=122),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=290),
    ],
    spell_icon_id=533,
    notes=(
        'rogue-rework S3a A2, Combat doc "Dual Wield Specialization": eff0 aura 122 off-hand damage +10% (stock), eff1 aura 290 MOD_CRIT_PCT +1 (S2 R10 shape).'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases your critical strike chance by $s2%. Increases the damage done by your off-hand weapon by $s1%.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        'ProcTypeMask': 0,
        **m.clear_mask_keys(0, 1, 2),
    },
)


improved_sinister_strike_13732 = spell(
    id=13732,
    name='Improved Sinister Strike',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=108, misc_value=0),
    ],
    spell_icon_id=130,
    notes=(
        'rogue-rework S3a A2, Combat doc "Improved Sinister Strike": eff0 pct DAMAGE +5 on IMPROVED_SS_READ (Sinister Strike and its second strike; stock was a flat energy cost reduction, now built into the 40 cost).'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the damage of your Sinister Strike by $s1%.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        'ProcTypeMask': 0,
        **m.read_mask_keys(0, m.IMPROVED_SS_READ),
        **m.clear_mask_keys(1, 2),
    },
)


puncturing_wounds_13733 = spell(
    id=13733,
    name='Puncturing Wounds',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=243,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Puncturing Wounds": values stock (Backstab 10/20/30, Mutilate 5/10/15); eff1 (Mutilate) re-masked from the stock hands\' d1 b1|b2 to MUTILATE_HAND_BITS (d2 b20: the new hands 203827 / 203828 carry only that bit, never d1 b1/b2). eff0 keeps Backstab (d0 b2).'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the critical strike chance of your Backstab ability by $s1%. Increases the critical strike chance of your Mutilate ability by $s2%.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EffectSpellClassMaskA_1': 4,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **_read_mask(2, m.MUTILATE_HAND_BITS),
    },
)


improved_gouge_13741 = spell(
    id=13741,
    name='Improved Gouge',
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
        Effect(type=EffectType.APPLY_AURA, base_points=499, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=245,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effect duration of your Gouge ability by $/1000;S1 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 8, 'EffectSpellClassMaskA_1': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)


endurance_13742 = spell(
    id=13742,
    name='Endurance',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-30001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=137, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=178,
    notes=(
        'rogue-rework S3a A2, Combat doc "Endurance": eff0 flat COOLDOWN -30000 ms on Evasion only (ENDURANCE_EVASION_READ; the Sprint clause is gone), eff1 Stamina +2% (stock), eff2 DUMMY 10 (Magic damage taken reduction %, read by the 204001 helper).'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Reduces the cooldown of your Evasion by $/1000;s1 sec. Increases your total Stamina by $s2%. You take $s3% less Magic damage while Evasion is active.',
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        'ProcTypeMask': 0,
        **m.read_mask_keys(0, m.ENDURANCE_EVASION_READ),
        **m.clear_mask_keys(1, 2),
    },
)


improved_sprint_13743 = spell(
    id=13743,
    name='Improved Sprint',
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
        Effect(type=EffectType.APPLY_AURA, base_points=999, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=516,
    notes=(
        'rogue-rework S3a A2, Combat doc "Improved Sprint": eff0 flat DURATION +1000 ms on Sprint (IMPROVED_SPRINT_DURATION_READ); the stock aura 109 chance moved to rank 2.'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': _with_cap('Increases the duration of Sprint by $/1000;s1 sec.', 'Capstone: Using Sprint removes all slow effects, and while Sprint is active the duration of root effects on you is reduced by $204000s1% and your movement speed can\'t be reduced below $204000s2% of normal.', False),
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        'ProcTypeMask': 0,
        **m.read_mask_keys(0, m.IMPROVED_SPRINT_DURATION_READ),
        **m.clear_mask_keys(1, 2),
    },
)


improved_kick_13754 = spell(
    id=13754,
    name='Improved Kick',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=18425),
    ],
    spell_icon_id=246,
    notes=(
        'rogue-rework S3a A2, Combat doc "Improved Kick": the stock 50% silence proc (row -13754, 18425) is kept; the capstone marker is rank 2\'s eff1 (Rogue::OnKickInterrupt reads HasAura(13867)).'
    ),
    raw_overrides={
        'AttributesEx3': 524288,
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': _with_cap('Gives your Kick a $h% chance to silence the target for $18425d.', 'Capstone: Your successful interrupts with Kick grant you $203999s1 energy and $203999s2% attack speed for $203999d.', False),
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 50,
        'ProcTypeMask': 87376,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **m.clear_mask_keys(0, 1, 2),
    },
)


improved_gouge_13792 = spell(
    id=13792,
    name='Improved Gouge',
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
        Effect(type=EffectType.APPLY_AURA, base_points=1499, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=245,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effect duration of your Gouge ability by $/1000;S1 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 8, 'EffectSpellClassMaskA_1': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)


improved_gouge_13793 = spell(
    id=13793,
    name='Improved Gouge',
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
        Effect(type=EffectType.APPLY_AURA, base_points=999, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=245,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effect duration of your Gouge ability by $/1000;S1 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 8, 'EffectSpellClassMaskA_1': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)


dual_wield_specialization_13848 = spell(
    id=13848,
    name='Dual Wield Specialization',
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
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=122),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=290),
    ],
    spell_icon_id=533,
    notes=(
        'rogue-rework S3a A2, Combat doc "Dual Wield Specialization": eff0 aura 122 off-hand damage +20% (stock), eff1 aura 290 MOD_CRIT_PCT +2 (S2 R10 shape).'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases your critical strike chance by $s2%. Increases the damage done by your off-hand weapon by $s1%.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        'ProcTypeMask': 0,
        **m.clear_mask_keys(0, 1, 2),
    },
)


dual_wield_specialization_13849 = spell(
    id=13849,
    name='Dual Wield Specialization',
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
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=122),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=290),
    ],
    spell_icon_id=533,
    notes=(
        'rogue-rework S3a A2, Combat doc "Dual Wield Specialization": eff0 aura 122 off-hand damage +30% (stock), eff1 aura 290 MOD_CRIT_PCT +3 (S2 R10 shape).'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases your critical strike chance by $s2%. Increases the damage done by your off-hand weapon by $s1%.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        'ProcTypeMask': 0,
        **m.clear_mask_keys(0, 1, 2),
    },
)


dual_wield_specialization_13851 = spell(
    id=13851,
    name='Dual Wield Specialization',
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
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=122),
    ],
    spell_icon_id=533,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your offhand weapon by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)


dual_wield_specialization_13852 = spell(
    id=13852,
    name='Dual Wield Specialization',
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
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=122),
    ],
    spell_icon_id=533,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your offhand weapon by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)


improved_sinister_strike_13863 = spell(
    id=13863,
    name='Improved Sinister Strike',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=0),
    ],
    spell_icon_id=130,
    notes=(
        'rogue-rework S3a A2, Combat doc "Improved Sinister Strike": eff0 pct DAMAGE +10 on IMPROVED_SS_READ (Sinister Strike and its second strike; stock was a flat energy cost reduction, now built into the 40 cost).'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the damage of your Sinister Strike by $s1%.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        'ProcTypeMask': 0,
        **m.read_mask_keys(0, m.IMPROVED_SS_READ),
        **m.clear_mask_keys(1, 2),
    },
)


puncturing_wounds_13865 = spell(
    id=13865,
    name='Puncturing Wounds',
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
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=243,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Puncturing Wounds": values stock (Backstab 10/20/30, Mutilate 5/10/15); eff1 (Mutilate) re-masked from the stock hands\' d1 b1|b2 to MUTILATE_HAND_BITS (d2 b20: the new hands 203827 / 203828 carry only that bit, never d1 b1/b2). eff0 keeps Backstab (d0 b2).'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the critical strike chance of your Backstab ability by $s1%. Increases the critical strike chance of your Mutilate ability by $s2%.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EffectSpellClassMaskA_1': 4,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **_read_mask(2, m.MUTILATE_HAND_BITS),
    },
)


puncturing_wounds_13866 = spell(
    id=13866,
    name='Puncturing Wounds',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=107, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=243,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Puncturing Wounds": values stock (Backstab 10/20/30, Mutilate 5/10/15); eff1 (Mutilate) re-masked from the stock hands\' d1 b1|b2 to MUTILATE_HAND_BITS (d2 b20: the new hands 203827 / 203828 carry only that bit, never d1 b1/b2). eff0 keeps Backstab (d0 b2).'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the critical strike chance of your Backstab ability by $s1%. Increases the critical strike chance of your Mutilate ability by $s2%.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EffectSpellClassMaskA_1': 4,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **_read_mask(2, m.MUTILATE_HAND_BITS),
    },
)


improved_kick_13867 = spell(
    id=13867,
    name='Improved Kick',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=18425),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=246,
    notes=(
        'rogue-rework S3a A2, Combat doc "Improved Kick": the stock 100% silence proc (row -13754, 18425) is kept; eff1 DUMMY 0 is the capstone marker (Rogue::OnKickInterrupt / spell_rog_kick_combat read HasAura(13867); buff 203999).'
    ),
    raw_overrides={
        'AttributesEx3': 524288,
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': _with_cap('Gives your Kick a $h% chance to silence the target for $18425d.', 'Capstone: Your successful interrupts with Kick grant you $203999s1 energy and $203999s2% attack speed for $203999d.', True),
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 100,
        'ProcTypeMask': 87376,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **m.clear_mask_keys(0, 1, 2),
    },
)


endurance_13872 = spell(
    id=13872,
    name='Endurance',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-60001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=137, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=178,
    notes=(
        'rogue-rework S3a A2, Combat doc "Endurance": eff0 flat COOLDOWN -60000 ms on Evasion only (ENDURANCE_EVASION_READ; the Sprint clause is gone), eff1 Stamina +4% (stock), eff2 DUMMY 20 (Magic damage taken reduction %, read by the 204001 helper).'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Reduces the cooldown of your Evasion by $/1000;s1 sec. Increases your total Stamina by $s2%. You take $s3% less Magic damage while Evasion is active.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        'ProcTypeMask': 0,
        **m.read_mask_keys(0, m.ENDURANCE_EVASION_READ),
        **m.clear_mask_keys(1, 2),
    },
)


improved_sprint_13875 = spell(
    id=13875,
    name='Improved Sprint',
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
        Effect(type=EffectType.APPLY_AURA, base_points=1999, implicit_target_a=1, apply_aura=107, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=109, trigger_spell=30918),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=516,
    notes=(
        'rogue-rework S3a A2, Combat doc "Improved Sprint": eff0 flat DURATION +2000 ms on Sprint, eff1 aura 109 -> 30918 (100%, slow removal; the stock effect moved here, IMPROVED_SPRINT_TRIGGER_READ), eff2 DUMMY 0 = the capstone marker (helper 204000 reads HasAura(13875)).'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': _with_cap('Increases the duration of Sprint by $/1000;s1 sec.', 'Capstone: Using Sprint removes all slow effects, and while Sprint is active the duration of root effects on you is reduced by $204000s1% and your movement speed can\'t be reduced below $204000s2% of normal.', True),
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        'ProcTypeMask': 0,
        **m.read_mask_keys(0, m.IMPROVED_SPRINT_DURATION_READ),
        **m.read_mask_keys(1, m.IMPROVED_SPRINT_TRIGGER_READ),
        **m.clear_mask_keys(2),
    },
)


camouflage_13975 = spell(
    id=13975,
    name='Camouflage',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=107, misc_value=23),
        Effect(type=EffectType.APPLY_AURA, base_points=-2001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=250,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Camouflage": stock effects unchanged (U45: Prowl stays text only); '
        "tooltip = the doc's verbatim (R5)."
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases your speed while stealthed or in Prowl by $s1%. Reduces the cooldown of your Stealth and Prowl abilities by $/1000;s2 sec.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EffectSpellClassMaskA_1': 4194304,
        'EffectSpellClassMaskB_1': 4194304,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        'SpellVisualID_1': 11336,
    },
)


initiative_13976 = spell(
    id=13976,
    name='Initiative',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=13977),
    ],
    spell_icon_id=233,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Initiative": eff0 aura 42 PROC_TRIGGER_SPELL -> 13977 (the stock '
        "ADD_COMBO_POINTS), raw ProcChance 33 (the rank's own chance, through Aura::CalcProcChance x Proc Chance), "
        "raw ProcTypeMask 0 (the spell_proc -13976 row below supplies the flags, C1). The ranks' A_1 0x700 is inert "
        'on aura 42.'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Gives you a $h% chance to gain an additional combo point when you use Ambush, Garrote or Cheap Shot.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EffectSpellClassMaskA_1': 1792,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 33,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        'ProcTypeMask': 0,
    },
)


initiative_13979 = spell(
    id=13979,
    name='Initiative',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=13977),
    ],
    spell_icon_id=233,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Initiative": eff0 aura 42 PROC_TRIGGER_SPELL -> 13977 (the stock '
        "ADD_COMBO_POINTS), raw ProcChance 66 (the rank's own chance, through Aura::CalcProcChance x Proc Chance), "
        "raw ProcTypeMask 0 (the spell_proc -13976 row below supplies the flags, C1). The ranks' A_1 0x700 is inert "
        'on aura 42.'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Gives you a $h% chance to gain an additional combo point when you use Ambush, Garrote or Cheap Shot.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EffectSpellClassMaskA_1': 1792,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 66,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        'ProcTypeMask': 0,
    },
)


initiative_13980 = spell(
    id=13980,
    name='Initiative',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=13977),
    ],
    spell_icon_id=233,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Initiative": eff0 aura 42 PROC_TRIGGER_SPELL -> 13977 (the stock '
        "ADD_COMBO_POINTS), raw ProcChance 100 (the rank's own chance, through Aura::CalcProcChance x Proc Chance), "
        "raw ProcTypeMask 0 (the spell_proc -13976 row below supplies the flags, C1). The ranks' A_1 0x700 is inert "
        'on aura 42.'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Gives you a $h% chance to gain an additional combo point when you use Ambush, Garrote or Cheap Shot.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EffectSpellClassMaskA_1': 1792,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 100,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        'ProcTypeMask': 0,
    },
)


elusiveness_13981 = spell(
    id=13981,
    name='Elusiveness',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-30001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=-15001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=331,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Elusiveness": eff0 flat COOLDOWN on Vanish only (ELUSIVENESS_VANISH_READ '
        'd0 b11; the stock Blind d0 b24 is dropped); eff1 Cloak of Shadows (B_2 65536) unchanged; tooltip = the '
        "doc's."
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Reduces the cooldown of your Vanish by $/1000;S1 sec and your Cloak of Shadows by $/1000;S2 sec.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EffectSpellClassMaskB_2': 65536,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **m.read_mask_keys(0, m.ELUSIVENESS_VANISH_READ),
    },
)


opportunity_14057 = spell(
    id=14057,
    name='From the Shadows',
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
    spell_icon_id=282,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "From the Shadows": renamed from Opportunity (Combat has its own). eff0 '
        'pct DAMAGE +10/20 on FROM_THE_SHADOWS_READ (Backstab d0 b2, Ambush d0 b9, Mutilate hands d2 b20; the stock '
        'd1 b1 / b2 hand bits are gone), eff1 pct DOT +10/20 on Garrote (FROM_THE_SHADOWS_DOT_READ). Tooltip is the '
        "stock text = the doc's."
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the damage dealt with your Backstab, Mutilate, Garrote and Ambush abilities by $s1%.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_2': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **m.read_mask_keys(0, m.FROM_THE_SHADOWS_READ),
        **m.read_mask_keys(1, m.FROM_THE_SHADOWS_DOT_READ),
    },
)


camouflage_14062 = spell(
    id=14062,
    name='Camouflage',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=23),
        Effect(type=EffectType.APPLY_AURA, base_points=-4001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=250,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Camouflage": stock effects unchanged (U45: Prowl stays text only); '
        "tooltip = the doc's verbatim (R5)."
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases your speed while stealthed or in Prowl by $s1%. Reduces the cooldown of your Stealth and Prowl abilities by $/1000;s2 sec.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EffectSpellClassMaskA_1': 4194304,
        'EffectSpellClassMaskB_1': 4194304,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        'SpellVisualID_1': 11335,
    },
)


camouflage_14063 = spell(
    id=14063,
    name='Camouflage',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=107, misc_value=23),
        Effect(type=EffectType.APPLY_AURA, base_points=-6001, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=250,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Camouflage": stock effects unchanged (U45: Prowl stays text only); '
        "tooltip = the doc's verbatim (R5)."
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases your speed while stealthed or in Prowl by $s1%. Reduces the cooldown of your Stealth and Prowl abilities by $/1000;s2 sec.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EffectSpellClassMaskA_1': 4194304,
        'EffectSpellClassMaskB_1': 4194304,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        'SpellVisualID_1': 11335,
    },
)


elusiveness_14066 = spell(
    id=14066,
    name='Elusiveness',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-60001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=-30001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=331,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Elusiveness": eff0 flat COOLDOWN on Vanish only (ELUSIVENESS_VANISH_READ '
        'd0 b11; the stock Blind d0 b24 is dropped); eff1 Cloak of Shadows (B_2 65536) unchanged; tooltip = the '
        "doc's."
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Reduces the cooldown of your Vanish by $/1000;S1 sec and your Cloak of Shadows by $/1000;S2 sec.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EffectSpellClassMaskB_2': 65536,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **m.read_mask_keys(0, m.ELUSIVENESS_VANISH_READ),
    },
)


opportunity_14072 = spell(
    id=14072,
    name='From the Shadows',
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
    spell_icon_id=282,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "From the Shadows": renamed from Opportunity (Combat has its own). eff0 '
        'pct DAMAGE +10/20 on FROM_THE_SHADOWS_READ (Backstab d0 b2, Ambush d0 b9, Mutilate hands d2 b20; the stock '
        'd1 b1 / b2 hand bits are gone), eff1 pct DOT +10/20 on Garrote (FROM_THE_SHADOWS_DOT_READ). Tooltip is the '
        "stock text = the doc's."
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the damage dealt with your Backstab, Mutilate, Garrote and Ambush abilities by $s1%.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_2': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **m.read_mask_keys(0, m.FROM_THE_SHADOWS_READ),
        **m.read_mask_keys(1, m.FROM_THE_SHADOWS_DOT_READ),
    },
)


dirty_tricks_14076 = spell(
    id=14076,
    name='Dirty Tricks',
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
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=5),
        Effect(type=EffectType.APPLY_AURA, base_points=-26, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=249,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of your Blind and Sap abilities by $s1 yards and reduces the energy cost of your Blind and Sap abilities by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': 16777344, 'EffectSpellClassMaskB_1': 16777344, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)


improved_ambush_14079 = spell(
    id=14079,
    name='Improved Ambush',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=856,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Improved Ambush": flat CRITICAL_CHANCE +15 on Ambush '
        '(IMPROVED_AMBUSH_READ; stock 25/50).'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the critical strike chance of your Ambush by $s1%.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **m.read_mask_keys(0, m.IMPROVED_AMBUSH_READ),
    },
)


improved_ambush_14080 = spell(
    id=14080,
    name='Improved Ambush',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=856,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Improved Ambush": flat CRITICAL_CHANCE +30 on Ambush '
        '(IMPROVED_AMBUSH_READ; stock 25/50).'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the critical strike chance of your Ambush by $s1%.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **m.read_mask_keys(0, m.IMPROVED_AMBUSH_READ),
    },
)


dirty_deeds_14082 = spell(
    id=14082,
    name='Dirty Deeds',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=107, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=112, misc_value=6427),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=112, misc_value=6580),
    ],
    spell_icon_id=216,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the Energy cost of your Cheap Shot and Garrote abilities by $s1.  Additionally, your special abilities cause 10% more damage against targets below 35% health.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1280, 'EffectSpellClassMaskB_1': 646054430, 'EffectSpellClassMaskB_2': 271, 'EffectSpellClassMaskC_1': 1048832, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)


dirty_deeds_14083 = spell(
    id=14083,
    name='Dirty Deeds',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=107, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=112, misc_value=6428),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=112, misc_value=6579),
    ],
    spell_icon_id=216,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the Energy cost of your Cheap Shot and Garrote abilities by $s1.  Additionally, your special abilities cause 20% more damage against targets below 35% health.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1280, 'EffectSpellClassMaskB_1': 646054430, 'EffectSpellClassMaskB_2': 271, 'EffectSpellClassMaskC_1': 1048832, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8, 'TargetAuraState': 13},
)


dirty_tricks_14094 = spell(
    id=14094,
    name='Dirty Tricks',
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
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=107, misc_value=5),
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=1, apply_aura=108, misc_value=14),
    ],
    spell_icon_id=249,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of your Blind and Sap abilities by $s1 yards and reduces the energy cost of your Blind and Sap abilities by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': 16777344, 'EffectSpellClassMaskB_1': 16777344, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)


improved_poisons_14113 = spell(
    id=14113,
    name='Improved Poisons',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=107, misc_value=18),
    ],
    spell_icon_id=247,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Improved Poisons": flat CHANCE_OF_SUCCESS +3/6/10 points on IMPROVED_POISONS_READ (the Lethal self auras 203701-203703, d2 b1: RollPoison adds it before Proc Chance multiplies); the stock PPM effect is gone. Rank 3 (14115) is the capstone: the Wound payload script reads its presence (Mastery / 2 into aura 271). Ranks 14116 / 14117 stay declared, unranked (A1).'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': "Increases the chance to apply your Instant, Deadly and Wound Poison by $s1%.\n\n|cFF9D9D9DCapstone: Wound Poison's bleed damage bonus is increased by half of your Mastery.|r",
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **_read_mask(1, m.IMPROVED_POISONS_READ),
    },
)


improved_poisons_14114 = spell(
    id=14114,
    name='Improved Poisons',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=107, misc_value=18),
    ],
    spell_icon_id=247,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Improved Poisons": flat CHANCE_OF_SUCCESS +3/6/10 points on IMPROVED_POISONS_READ (the Lethal self auras 203701-203703, d2 b1: RollPoison adds it before Proc Chance multiplies); the stock PPM effect is gone. Rank 3 (14115) is the capstone: the Wound payload script reads its presence (Mastery / 2 into aura 271). Ranks 14116 / 14117 stay declared, unranked (A1).'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': "Increases the chance to apply your Instant, Deadly and Wound Poison by $s1%.\n\n|cFF9D9D9DCapstone: Wound Poison's bleed damage bonus is increased by half of your Mastery.|r",
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **_read_mask(1, m.IMPROVED_POISONS_READ),
    },
)


improved_poisons_14115 = spell(
    id=14115,
    name='Improved Poisons',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=18),
    ],
    spell_icon_id=247,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Improved Poisons": flat CHANCE_OF_SUCCESS +3/6/10 points on IMPROVED_POISONS_READ (the Lethal self auras 203701-203703, d2 b1: RollPoison adds it before Proc Chance multiplies); the stock PPM effect is gone. Rank 3 (14115) is the capstone: the Wound payload script reads its presence (Mastery / 2 into aura 271). Ranks 14116 / 14117 stay declared, unranked (A1).'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': "Increases the chance to apply your Instant, Deadly and Wound Poison by $s1%.\n\nCapstone: Wound Poison's bleed damage bonus is increased by half of your Mastery.",
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **_read_mask(1, m.IMPROVED_POISONS_READ),
    },
)


improved_poisons_14116 = spell(
    id=14116,
    name='Improved Poisons',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=107, misc_value=18),
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=108, misc_value=26),
    ],
    spell_icon_id=247,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the chance to apply Deadly Poison to your target by $s1% and the frequency of applying Instant Poison to your target by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 65536, 'EffectSpellClassMaskB_1': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)


improved_poisons_14117 = spell(
    id=14117,
    name='Improved Poisons',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=107, misc_value=18),
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=108, misc_value=26),
    ],
    spell_icon_id=247,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the chance to apply Deadly Poison to your target by $s1% and the frequency of applying Instant Poison to your target by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 65536, 'EffectSpellClassMaskB_1': 8192, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)


lethality_14128 = spell(
    id=14128,
    name='Lethality',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=138,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Lethality": pct CRIT_DAMAGE_BONUS +10/20/30% on LETHALITY_READ: single-strike builders (d2 b19: Ambush and Gouge included, U11), Mutilate hands (d2 b20), Kingsbane hands (d2 b10), Fan of Knives (d1 b18, both ids), Instant (d0 b13) and Wound (d0 b28) hits. Not periodic: no Deadly Poison, no bleeds. Outside spell_group 1201 (U16). Ranks 14136 / 14137 stay declared, unranked (A1).'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the critical strike damage bonus of all non-periodic combo point-generating Rogue abilities and Rogue poisons by $s1%.',
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **_read_mask(1, m.LETHALITY_READ),
    },
)


lethality_14132 = spell(
    id=14132,
    name='Lethality',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=138,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Lethality": pct CRIT_DAMAGE_BONUS +10/20/30% on LETHALITY_READ: single-strike builders (d2 b19: Ambush and Gouge included, U11), Mutilate hands (d2 b20), Kingsbane hands (d2 b10), Fan of Knives (d1 b18, both ids), Instant (d0 b13) and Wound (d0 b28) hits. Not periodic: no Deadly Poison, no bleeds. Outside spell_group 1201 (U16). Ranks 14136 / 14137 stay declared, unranked (A1).'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the critical strike damage bonus of all non-periodic combo point-generating Rogue abilities and Rogue poisons by $s1%.',
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **_read_mask(1, m.LETHALITY_READ),
    },
)


lethality_14135 = spell(
    id=14135,
    name='Lethality',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=138,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Lethality": pct CRIT_DAMAGE_BONUS +10/20/30% on LETHALITY_READ: single-strike builders (d2 b19: Ambush and Gouge included, U11), Mutilate hands (d2 b20), Kingsbane hands (d2 b10), Fan of Knives (d1 b18, both ids), Instant (d0 b13) and Wound (d0 b28) hits. Not periodic: no Deadly Poison, no bleeds. Outside spell_group 1201 (U16). Ranks 14136 / 14137 stay declared, unranked (A1).'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the critical strike damage bonus of all non-periodic combo point-generating Rogue abilities and Rogue poisons by $s1%.',
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **_read_mask(1, m.LETHALITY_READ),
    },
)


lethality_14136 = spell(
    id=14136,
    name='Lethality',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=23, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=138,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of all combo point-generating abilities that do not require stealth by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 637534222, 'EffectSpellClassMaskA_2': 262, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)


lethality_14137 = spell(
    id=14137,
    name='Lethality',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=138,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of all combo point-generating abilities that do not require stealth by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 637534222, 'EffectSpellClassMaskA_2': 262, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)


ruthlessness_14156 = spell(
    id=14156,
    name='Ruthlessness',
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
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=108, misc_value=0),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=494,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Ruthlessness": eff0 pct DAMAGE and eff1 pct DOT +1/2/3% on RUTHLESSNESS_READ (the finisher group d2 b18; Rupture is a DoT), eff2 DUMMY 33/66/100 = the combo point chance Rogue::OnSpellCast reads (R13). The stock proc effect (aura 42 -> 14157) is gone; ProcTypeMask 0 / ProcChance 101 (R8) so no default proc entry appears once spell_proc -14156 is removed. 9 s ICD is RogueData::RUTHLESSNESS_ICD_MS.'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the damage of your Rogue finishing moves by $s1%. Your Rogue melee weapon finishing moves have a $s3% chance to add a combo point. This effect cannot occur more than once every 9 sec.',
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'ProcTypeMask': 0,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **_read_mask(1, m.RUTHLESSNESS_READ_S3),
        **_read_mask(2, m.RUTHLESSNESS_READ_S3),
    },
)


murder_14158 = spell(
    id=14158,
    name='Murder',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=79, misc_value=9),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=134,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Murder": eff0 aura 79 MOD_DAMAGE_PERCENT_DONE misc 9 (Physical | Nature, stock 255) +1/2% (stock +2/4%); the stock class mask on aura 79 was inert and is gone. eff1 pct DOT +5/10 on Garrote (MURDER_DOT_READ). Doomblade\'s tick ignores it (IGNORE_CASTER_MODIFIERS).'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases all Physical and Nature damage caused by $s1%. Increases the damage from Garrote by $s2%.',
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **_read_mask(2, m.MURDER_DOT_READ),
    },
)


murder_14159 = spell(
    id=14159,
    name='Murder',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=79, misc_value=9),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=134,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Murder": eff0 aura 79 MOD_DAMAGE_PERCENT_DONE misc 9 (Physical | Nature, stock 255) +1/2% (stock +2/4%); the stock class mask on aura 79 was inert and is gone. eff1 pct DOT +5/10 on Garrote (MURDER_DOT_READ). Doomblade\'s tick ignores it (IGNORE_CASTER_MODIFIERS).'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases all Physical and Nature damage caused by $s1%. Increases the damage from Garrote by $s2%.',
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **_read_mask(2, m.MURDER_DOT_READ),
    },
)


ruthlessness_14160 = spell(
    id=14160,
    name='Ruthlessness',
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
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=108, misc_value=0),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=65, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=494,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Ruthlessness": eff0 pct DAMAGE and eff1 pct DOT +1/2/3% on RUTHLESSNESS_READ (the finisher group d2 b18; Rupture is a DoT), eff2 DUMMY 33/66/100 = the combo point chance Rogue::OnSpellCast reads (R13). The stock proc effect (aura 42 -> 14157) is gone; ProcTypeMask 0 / ProcChance 101 (R8) so no default proc entry appears once spell_proc -14156 is removed. 9 s ICD is RogueData::RUTHLESSNESS_ICD_MS.'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the damage of your Rogue finishing moves by $s1%. Your Rogue melee weapon finishing moves have a $s3% chance to add a combo point. This effect cannot occur more than once every 9 sec.',
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'ProcTypeMask': 0,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **_read_mask(1, m.RUTHLESSNESS_READ_S3),
        **_read_mask(2, m.RUTHLESSNESS_READ_S3),
    },
)


ruthlessness_14161 = spell(
    id=14161,
    name='Ruthlessness',
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
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=108, misc_value=0),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=494,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Ruthlessness": eff0 pct DAMAGE and eff1 pct DOT +1/2/3% on RUTHLESSNESS_READ (the finisher group d2 b18; Rupture is a DoT), eff2 DUMMY 33/66/100 = the combo point chance Rogue::OnSpellCast reads (R13). The stock proc effect (aura 42 -> 14157) is gone; ProcTypeMask 0 / ProcChance 101 (R8) so no default proc entry appears once spell_proc -14156 is removed. 9 s ICD is RogueData::RUTHLESSNESS_ICD_MS.'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the damage of your Rogue finishing moves by $s1%. Your Rogue melee weapon finishing moves have a $s3% chance to add a combo point. This effect cannot occur more than once every 9 sec.',
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'ProcTypeMask': 0,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **_read_mask(1, m.RUTHLESSNESS_READ_S3),
        **_read_mask(2, m.RUTHLESSNESS_READ_S3),
    },
)


improved_eviscerate_14162 = spell(
    id=14162,
    name='Improved Eviscerate',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=514,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Eviscerate ability by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)


improved_eviscerate_14163 = spell(
    id=14163,
    name='Improved Eviscerate',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=13, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=514,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Eviscerate ability by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)


improved_eviscerate_14164 = spell(
    id=14164,
    name='Improved Eviscerate',
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
    ],
    spell_icon_id=514,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Eviscerate ability by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)


improved_slice_and_dice_14165 = spell(
    id=14165,
    name='Improved Slice and Dice',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=108, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=107, misc_value=12),
    ],
    spell_icon_id=515,
    notes=(
        'rogue-rework S3a A2, Combat doc "Improved Slice and Dice": eff0 pct DURATION +25 (stock), eff1 flat EFFECT2 +3 on Slice and Dice\'s index-1 aura 138 (attack speed), both on IMPROVED_SND_READ.'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the duration of your Slice and Dice by $s1% and the attack speed it grants by $s2%.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        'ProcTypeMask': 0,
        **m.read_mask_keys(0, m.IMPROVED_SND_READ),
        **m.read_mask_keys(1, m.IMPROVED_SND_READ),
        **m.clear_mask_keys(2),
    },
)


improved_slice_and_dice_14166 = spell(
    id=14166,
    name='Improved Slice and Dice',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=108, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=107, misc_value=12),
    ],
    spell_icon_id=515,
    notes=(
        'rogue-rework S3a A2, Combat doc "Improved Slice and Dice": eff0 pct DURATION +50 (stock), eff1 flat EFFECT2 +6 on Slice and Dice\'s index-1 aura 138 (attack speed), both on IMPROVED_SND_READ.'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the duration of your Slice and Dice by $s1% and the attack speed it grants by $s2%.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        'ProcTypeMask': 0,
        **m.read_mask_keys(0, m.IMPROVED_SND_READ),
        **m.read_mask_keys(1, m.IMPROVED_SND_READ),
        **m.clear_mask_keys(2),
    },
)


improved_expose_armor_14168 = spell(
    id=14168,
    name='Improved Expose Armor',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-6, implicit_target_a=1, apply_aura=107, misc_value=14),
    ],
    spell_icon_id=563,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the energy cost of your Expose Armor ability by $s1.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 524288, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)


improved_expose_armor_14169 = spell(
    id=14169,
    name='Improved Expose Armor',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=107, misc_value=14),
    ],
    spell_icon_id=563,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the energy cost of your Expose Armor ability by $s1.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 524288, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)


serrated_blades_14171 = spell(
    id=14171,
    name='Serrated Blades',
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
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=280, misc_value=1),
    ],
    spell_icon_id=2004,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Serrated Blades": stock values (eff0 pct DOT +10/20/30 on Rupture = '
        "SERRATED_BLADES_DOT_READ, eff1 aura 280 +3/6/9); tooltip = the doc's verbatim (R5)."
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': "Your attacks ignore $s2% of your target's armor, and your Rupture deals $s1% more damage.",
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **m.read_mask_keys(0, m.SERRATED_BLADES_DOT_READ),
    },
)


serrated_blades_14172 = spell(
    id=14172,
    name='Serrated Blades',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=280, misc_value=1),
    ],
    spell_icon_id=2004,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Serrated Blades": stock values (eff0 pct DOT +10/20/30 on Rupture = '
        "SERRATED_BLADES_DOT_READ, eff1 aura 280 +3/6/9); tooltip = the doc's verbatim (R5)."
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': "Your attacks ignore $s2% of your target's armor, and your Rupture deals $s1% more damage.",
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **m.read_mask_keys(0, m.SERRATED_BLADES_DOT_READ),
    },
)


serrated_blades_14173 = spell(
    id=14173,
    name='Serrated Blades',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=280, misc_value=1),
    ],
    spell_icon_id=2004,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Serrated Blades": stock values (eff0 pct DOT +10/20/30 on Rupture = '
        "SERRATED_BLADES_DOT_READ, eff1 aura 280 +3/6/9); tooltip = the doc's verbatim (R5)."
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': "Your attacks ignore $s2% of your target's armor, and your Rupture deals $s1% more damage.",
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **m.read_mask_keys(0, m.SERRATED_BLADES_DOT_READ),
    },
)


improved_kidney_shot_14174 = spell(
    id=14174,
    name='Improved Kidney Shot',
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
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=107, misc_value=8),
    ],
    spell_icon_id=499,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While affected by your Kidney Shot ability, the target receives an additional $s1% damage from all sources.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 2097152, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)


improved_kidney_shot_14175 = spell(
    id=14175,
    name='Improved Kidney Shot',
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
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=107, misc_value=8),
    ],
    spell_icon_id=499,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While affected by your Kidney Shot ability, the target receives an additional $s1% damage from all sources.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 2097152, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)


improved_kidney_shot_14176 = spell(
    id=14176,
    name='Improved Kidney Shot',
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
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=107, misc_value=8),
    ],
    spell_icon_id=499,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While affected by your Kidney Shot ability, the target receives an additional $s1% damage from all sources.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectSpellClassMaskA_1': 2097152, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)


relentless_strikes_14179 = spell(
    id=14179,
    name='Relentless Strikes',
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
    spell_icon_id=559,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Relentless Strikes": eff0 hidden DUMMY 10 (the % chance per combo point; '
        'read by GetRankAmount EFFECT_0). The stock aura 109 -> 14181 is gone (the dispatcher rolls it and casts '
        '14181 + 204155); stale A_1 0x3E0000 / A_2 9 cleared; EffectPointsPerCombo_1 zeroed (SpellInfo::CalcValue '
        "adds PointsPerComboPoint x the caster's combo points to a DUMMY value)."
    ),
    raw_overrides={
        'AttributesEx': 1048576,
        'AttributesEx4': 2,
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': "Your finishing moves have a $s1% chance per combo point to restore $14181s1 energy and to cause your attacks to ignore $204155s1% of your target's armor for $204155d.",
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EffectPointsPerCombo_1': 0.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **m.clear_mask_keys(0),
    },
)


seal_fate_14186 = spell(
    id=14186,
    name='Seal Fate',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=14189),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=0),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=55,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Seal Fate": ProcChance 33/66/100 (stock 20/40/60); eff0 stays the proc (aura 42 -> 14189, ADD_COMBO_POINTS); the spell_proc -14186 row below narrows it to single-strike builders (d2 b19, C2); multi-hit casts roll through Rogue::RollSealFate. eff1 pct DAMAGE +10 on Eviscerate + Deadly Throw (SEAL_FATE_DAMAGE_READ), eff2 pct DOT +10 on Rupture (SEAL_FATE_DOT_READ), all ranks. Capstone (14193): Cold Blood consumption, B2 script -> 203834. Ranks 14194 / 14195 stay declared, unranked.'
    ),
    raw_overrides={
        'AttributesEx3': 524288,
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Your critical strikes from Rogue abilities that add combo points have a $h% chance to add an additional combo point. Increases the damage done by Eviscerate, Rupture and Deadly Throw by $s2%.\n\n|cFF9D9D9DCapstone: Consuming Cold Blood with a finishing move has a 20% chance per combo point to increase your movement speed by $203834s1% for $203834d.|r',
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 33,
        'ProcTypeMask': 87376,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        'SpellLevel': 1,
        'SpellPriority': 50,
        **_read_mask(2, m.SEAL_FATE_DAMAGE_READ),
        **_read_mask(3, m.SEAL_FATE_DOT_READ),
    },
)


seal_fate_14190 = spell(
    id=14190,
    name='Seal Fate',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=14189),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=0),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=55,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Seal Fate": ProcChance 33/66/100 (stock 20/40/60); eff0 stays the proc (aura 42 -> 14189, ADD_COMBO_POINTS); the spell_proc -14186 row below narrows it to single-strike builders (d2 b19, C2); multi-hit casts roll through Rogue::RollSealFate. eff1 pct DAMAGE +10 on Eviscerate + Deadly Throw (SEAL_FATE_DAMAGE_READ), eff2 pct DOT +10 on Rupture (SEAL_FATE_DOT_READ), all ranks. Capstone (14193): Cold Blood consumption, B2 script -> 203834. Ranks 14194 / 14195 stay declared, unranked.'
    ),
    raw_overrides={
        'AttributesEx3': 524288,
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Your critical strikes from Rogue abilities that add combo points have a $h% chance to add an additional combo point. Increases the damage done by Eviscerate, Rupture and Deadly Throw by $s2%.\n\n|cFF9D9D9DCapstone: Consuming Cold Blood with a finishing move has a 20% chance per combo point to increase your movement speed by $203834s1% for $203834d.|r',
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 66,
        'ProcTypeMask': 87376,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        'SpellLevel': 1,
        'SpellPriority': 50,
        **_read_mask(2, m.SEAL_FATE_DAMAGE_READ),
        **_read_mask(3, m.SEAL_FATE_DOT_READ),
    },
)


seal_fate_14193 = spell(
    id=14193,
    name='Seal Fate',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=14189),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=0),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=55,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Seal Fate": ProcChance 33/66/100 (stock 20/40/60); eff0 stays the proc (aura 42 -> 14189, ADD_COMBO_POINTS); the spell_proc -14186 row below narrows it to single-strike builders (d2 b19, C2); multi-hit casts roll through Rogue::RollSealFate. eff1 pct DAMAGE +10 on Eviscerate + Deadly Throw (SEAL_FATE_DAMAGE_READ), eff2 pct DOT +10 on Rupture (SEAL_FATE_DOT_READ), all ranks. Capstone (14193): Cold Blood consumption, B2 script -> 203834. Ranks 14194 / 14195 stay declared, unranked.'
    ),
    raw_overrides={
        'AttributesEx3': 524288,
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Your critical strikes from Rogue abilities that add combo points have a $h% chance to add an additional combo point. Increases the damage done by Eviscerate, Rupture and Deadly Throw by $s2%.\n\nCapstone: Consuming Cold Blood with a finishing move has a 20% chance per combo point to increase your movement speed by $203834s1% for $203834d.',
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 100,
        'ProcTypeMask': 87376,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        'SpellLevel': 1,
        'SpellPriority': 50,
        **_read_mask(2, m.SEAL_FATE_DAMAGE_READ),
        **_read_mask(3, m.SEAL_FATE_DOT_READ),
    },
)


seal_fate_14194 = spell(
    id=14194,
    name='Seal Fate',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=14189),
    ],
    spell_icon_id=55,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your critical strikes from abilities that add combo points have a $h% chance to add an additional combo point.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 80, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellLevel': 1, 'SpellPriority': 50},
)


seal_fate_14195 = spell(
    id=14195,
    name='Seal Fate',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=14189),
    ],
    spell_icon_id=55,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your critical strikes from abilities that add combo points have a $h% chance to add an additional combo point.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellLevel': 1, 'SpellPriority': 50},
)


vigor_14983 = spell(
    id=14983,
    name='Vigor',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=35, misc_value=3),
    ],
    spell_icon_id=691,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Vigor": rank 1: aura 35 MOD_INCREASE_ENERGY misc 3 stored 14 = +15 maximum energy (stock +10); rank 2 is 203823 (+30, A3).'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases your maximum Energy by $s1.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_2': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712188,
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassMask_2': 4194304,
        'SpellClassSet': 8,
    },
)


vile_poisons_16513 = spell(
    id=16513,
    name='Vile Poisons',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=0),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=108, misc_value=3),
    ],
    spell_icon_id=857,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Vile Poisons": eff0 pct DAMAGE and eff1 pct DOT +10/20/30 on POISON_DAMAGE_READ (the poison group d1 b19: all six payloads + Envenom + Kingsbane / Shattering Vial / Blindside carriers), eff2 pct EFFECT1 +5/10/15 on Mind-numbing (VILE_POISONS_MIND_NUMBING_READ); the stock dispel-resist clause is gone. No free effect slot is left, so the Wound Poison duration clause is the linked helper 203844 (A3, spell_linked_spell type 2). Rank 3 is the Mastery capstone (203846 polls and moves eff0 / eff1 to 30 + Mastery).'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the damage dealt by your Rogue poisons and Envenom ability by $s1%. Increases the effectiveness of your Mind-Numbing Poison by $s3%. Increases the duration of your Wound Poison by $/1000;203844s1 sec.\n\n|cFF9D9D9DCapstone: The poison and Envenom damage bonus is increased by your Mastery.|r',
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **_read_mask(1, m.POISON_DAMAGE_READ),
        **_read_mask(2, m.POISON_DAMAGE_READ),
        **_read_mask(3, m.VILE_POISONS_MIND_NUMBING_READ),
    },
)


vile_poisons_16514 = spell(
    id=16514,
    name='Vile Poisons',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=0),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=3),
    ],
    spell_icon_id=857,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Vile Poisons": eff0 pct DAMAGE and eff1 pct DOT +10/20/30 on POISON_DAMAGE_READ (the poison group d1 b19: all six payloads + Envenom + Kingsbane / Shattering Vial / Blindside carriers), eff2 pct EFFECT1 +5/10/15 on Mind-numbing (VILE_POISONS_MIND_NUMBING_READ); the stock dispel-resist clause is gone. No free effect slot is left, so the Wound Poison duration clause is the linked helper 203845 (A3, spell_linked_spell type 2). Rank 3 is the Mastery capstone (203846 polls and moves eff0 / eff1 to 30 + Mastery).'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the damage dealt by your Rogue poisons and Envenom ability by $s1%. Increases the effectiveness of your Mind-Numbing Poison by $s3%. Increases the duration of your Wound Poison by $/1000;203845s1 sec.\n\n|cFF9D9D9DCapstone: The poison and Envenom damage bonus is increased by your Mastery.|r',
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **_read_mask(1, m.POISON_DAMAGE_READ),
        **_read_mask(2, m.POISON_DAMAGE_READ),
        **_read_mask(3, m.VILE_POISONS_MIND_NUMBING_READ),
    },
)


vile_poisons_16515 = spell(
    id=16515,
    name='Vile Poisons',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108, misc_value=0),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108, misc_value=3),
    ],
    spell_icon_id=857,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Vile Poisons": eff0 pct DAMAGE and eff1 pct DOT +10/20/30 on POISON_DAMAGE_READ (the poison group d1 b19: all six payloads + Envenom + Kingsbane / Shattering Vial / Blindside carriers), eff2 pct EFFECT1 +5/10/15 on Mind-numbing (VILE_POISONS_MIND_NUMBING_READ); the stock dispel-resist clause is gone. No free effect slot is left, so the Wound Poison duration clause is the linked helper 203846 (A3, spell_linked_spell type 2). Rank 3 is the Mastery capstone (203846 polls and moves eff0 / eff1 to 30 + Mastery).'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the damage dealt by your Rogue poisons and Envenom ability by $s1%. Increases the effectiveness of your Mind-Numbing Poison by $s3%. Increases the duration of your Wound Poison by $/1000;203846s1 sec.\n\nCapstone: The poison and Envenom damage bonus is increased by your Mastery.',
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **_read_mask(1, m.POISON_DAMAGE_READ),
        **_read_mask(2, m.POISON_DAMAGE_READ),
        **_read_mask(3, m.VILE_POISONS_MIND_NUMBING_READ),
    },
)


aggression_18427 = spell(
    id=18427,
    name='Aggression',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=84,
    notes=(
        'rogue-rework S3a A2, Combat doc "Aggression": eff0 flat CRITICAL_CHANCE +5 on AGGRESSION_READ (Sinister Strike, Pistol Shot, Eviscerate, Between the Eyes, the second strike, the extra shots); the stock pct DAMAGE is gone.'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the critical strike chance of your Sinister Strike, Pistol Shot, Eviscerate and Between the Eyes by $s1%.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_2': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        'ProcTypeMask': 0,
        **m.read_mask_keys(0, m.AGGRESSION_READ),
        **m.clear_mask_keys(1, 2),
    },
)


aggression_18428 = spell(
    id=18428,
    name='Aggression',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=84,
    notes=(
        'rogue-rework S3a A2, Combat doc "Aggression": eff0 flat CRITICAL_CHANCE +10 on AGGRESSION_READ (Sinister Strike, Pistol Shot, Eviscerate, Between the Eyes, the second strike, the extra shots); the stock pct DAMAGE is gone.'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the critical strike chance of your Sinister Strike, Pistol Shot, Eviscerate and Between the Eyes by $s1%.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_2': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        'ProcTypeMask': 0,
        **m.read_mask_keys(0, m.AGGRESSION_READ),
        **m.clear_mask_keys(1, 2),
    },
)


aggression_18429 = spell(
    id=18429,
    name='Aggression',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=84,
    notes=(
        'rogue-rework S3a A2, Combat doc "Aggression": eff0 flat CRITICAL_CHANCE +15 on AGGRESSION_READ (Sinister Strike, Pistol Shot, Eviscerate, Between the Eyes, the second strike, the extra shots); the stock pct DAMAGE is gone.'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the critical strike chance of your Sinister Strike, Pistol Shot, Eviscerate and Between the Eyes by $s1%.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_2': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        'ProcTypeMask': 0,
        **m.read_mask_keys(0, m.AGGRESSION_READ),
        **m.clear_mask_keys(1, 2),
    },
)


sleight_of_hand_30892 = spell(
    id=30892,
    name='Sleight of Hand',
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
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=-2, implicit_target_a=1, apply_aura=187),
        Effect(type=EffectType.APPLY_AURA, base_points=-2, implicit_target_a=1, apply_aura=188),
    ],
    spell_icon_id=539,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the chance you are critically hit by melee and ranged attacks by $s2% and increases the threat reduction of your Feint ability by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 134217728, 'EffectSpellClassMaskB_1': 134217728, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)


sleight_of_hand_30893 = spell(
    id=30893,
    name='Sleight of Hand',
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
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=8),
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=187),
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=188),
    ],
    spell_icon_id=539,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the chance you are critically hit by melee and ranged attacks by $s2% and increases the threat reduction of your Feint ability by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 134217728, 'EffectSpellClassMaskB_1': 134217728, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)


blade_twisting_31124 = spell(
    id=31124,
    name='Blade Twisting',
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
    ],
    spell_icon_id=2108,
    notes=(
        'rogue-rework S3a A2, Combat doc "Blade Twisting": eff0 DUMMY 2 (% damage per stack = the debuff 203998\'s bp, read by GetRankAmount); the stock daze proc and pct DAMAGE are gone (raw ProcTypeMask 0, spell_proc -31124 removed).'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Your Sinister Strike, Pistol Shot, Ghostly Strike, Riposte and Backstab apply Blade Twisting to the target, stacking up to $203998u times. Each stack increases the damage your combo point builders deal to that target by $s1%. Lasts $203998d.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'ProcTypeMask': 0,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **m.clear_mask_keys(0, 1, 2),
    },
)


blade_twisting_31126 = spell(
    id=31126,
    name='Blade Twisting',
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
    ],
    spell_icon_id=2108,
    notes=(
        'rogue-rework S3a A2, Combat doc "Blade Twisting": eff0 DUMMY 4 (% damage per stack = the debuff 203998\'s bp, read by GetRankAmount); the stock daze proc and pct DAMAGE are gone (raw ProcTypeMask 0, spell_proc -31124 removed).'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Your Sinister Strike, Pistol Shot, Ghostly Strike, Riposte and Backstab apply Blade Twisting to the target, stacking up to $203998u times. Each stack increases the damage your combo point builders deal to that target by $s1%. Lasts $203998d.',
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'ProcTypeMask': 0,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **m.clear_mask_keys(0, 1, 2),
    },
)


sinister_calling_31216 = spell(
    id=31216,
    name='Sinister Calling',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=137, misc_value=1),
    ],
    spell_icon_id=2118,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Sinister Calling": eff0 aura 137 MOD_TOTAL_STAT_PERCENTAGE Agility +1%; '
        'the stock Backstab / Hemorrhage damage effect (aura 108, stale B_1 0x2000004) is gone. The capstone (31218 '
        'held) is read by Rogue::OnSpellCast (the volley 204165).'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': _sinister_calling_text(False),
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **m.clear_mask_keys(1),
    },
)


sinister_calling_31217 = spell(
    id=31217,
    name='Sinister Calling',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=137, misc_value=1),
    ],
    spell_icon_id=2118,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Sinister Calling": eff0 aura 137 MOD_TOTAL_STAT_PERCENTAGE Agility +2%; '
        'the stock Backstab / Hemorrhage damage effect (aura 108, stale B_1 0x2000004) is gone. The capstone (31218 '
        'held) is read by Rogue::OnSpellCast (the volley 204165).'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': _sinister_calling_text(False),
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **m.clear_mask_keys(1),
    },
)


sinister_calling_31218 = spell(
    id=31218,
    name='Sinister Calling',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=137, misc_value=1),
    ],
    spell_icon_id=2118,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Sinister Calling": eff0 aura 137 MOD_TOTAL_STAT_PERCENTAGE Agility +3%; '
        'the stock Backstab / Hemorrhage damage effect (aura 108, stale B_1 0x2000004) is gone. The capstone (31218 '
        'held) is read by Rogue::OnSpellCast (the volley 204165).'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': _sinister_calling_text(True),
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **m.clear_mask_keys(1),
    },
)


sinister_calling_31219 = spell(
    id=31219,
    name='Sinister Calling',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=137, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=108, misc_value=12),
    ],
    spell_icon_id=2118,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Agility by $s1% and increases the percentage damage bonus of Backstab and Hemorrhage by an additional $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 33554436, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)


sinister_calling_31220 = spell(
    id=31220,
    name='Sinister Calling',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=137, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=12),
    ],
    spell_icon_id=2118,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Agility by $s1% and increases the percentage damage bonus of Backstab and Hemorrhage by an additional $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 33554436, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)


master_of_subtlety_31223 = spell(
    id=31223,
    name='Master of Subtlety',
    school=School.NORMAL,
    attributes=131536,
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
    spell_icon_id=2114,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Attacks made while stealthed and for 6 seconds after breaking stealth cause an additional $s1% damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194304, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)


master_poisoner_31226 = spell(
    id=31226,
    name='Master Poisoner',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=231, misc_value=23, trigger_spell=45176),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=246, misc_value=4),
    ],
    spell_icon_id=1960,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Master Poisoner": eff0 (aura 231 -> 45176, crit 1/2/3) and the raw EffectBasePoints_3 / EffectDieSides_3 (Envenom keep chance 33/66/100, read by SpellEffects.cpp:589-593 off Effects[2]) are stock and load-bearing (R6); icon 1960 and the 231 / 246 effect order unchanged. eff1 aura 246 misc 4 rewritten -17/34/50 -> -10/20/30. Rank 3 (58410) is the capstone: Rogue::GetLethalSlots returns 2 while it is held.'
    ),
    raw_overrides={
        'AttributesEx3': 67108864,
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the critical strike chance of all spells and attacks made against any target you have poisoned by $s1%, reduces the duration of all Poison effects applied to you by $s2%, and gives Envenom a $s3% chance not to consume Deadly Poison. Does not stack with other similar effects.\n\n|cFF9D9D9DCapstone: You may have two Lethal poisons active at once.|r',
        'EffectBasePoints_3': 32,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EffectDieSides_3': 1,
        'EffectSpellClassMaskA_2': 524288,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 100,
        'ProcTypeMask': 69632,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        'SpellLevel': 1,
        'SpellPriority': 50,
    },
)


master_poisoner_31227 = spell(
    id=31227,
    name='Master Poisoner',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=231, misc_value=23, trigger_spell=45176),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=246, misc_value=4),
    ],
    spell_icon_id=1960,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Master Poisoner": eff0 (aura 231 -> 45176, crit 1/2/3) and the raw EffectBasePoints_3 / EffectDieSides_3 (Envenom keep chance 33/66/100, read by SpellEffects.cpp:589-593 off Effects[2]) are stock and load-bearing (R6); icon 1960 and the 231 / 246 effect order unchanged. eff1 aura 246 misc 4 rewritten -17/34/50 -> -10/20/30. Rank 3 (58410) is the capstone: Rogue::GetLethalSlots returns 2 while it is held.'
    ),
    raw_overrides={
        'AttributesEx3': 67108864,
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the critical strike chance of all spells and attacks made against any target you have poisoned by $s1%, reduces the duration of all Poison effects applied to you by $s2%, and gives Envenom a $s3% chance not to consume Deadly Poison. Does not stack with other similar effects.\n\n|cFF9D9D9DCapstone: You may have two Lethal poisons active at once.|r',
        'EffectBasePoints_3': 65,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EffectDieSides_3': 1,
        'EffectSpellClassMaskA_2': 524288,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 100,
        'ProcTypeMask': 69632,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        'SpellLevel': 1,
        'SpellPriority': 50,
    },
)


cheat_death_31228 = spell(
    id=31228,
    name='Cheat Death',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(
            type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=1, apply_aura=69, misc_value=127,
            potency_excluded='not a damage/absorb value despite the SCHOOL_ABSORB(69) aura type and the '
            'P3 report classifying it as "absorb": spell_rog_cheat_death::CalculateAmount '
            '(src/server/scripts/Spells/spell_rogue.cpp) sets amount=-1 (unlimited) unconditionally and '
            'reads this effect\'s own CalcValue() as absorbChance, a roll_chance_i() PROC CHANCE PERCENT, '
            'not a shield size - the real absorbed amount is computed dynamically in Absorb() from the '
            'incoming hit and the target\'s current health, with no dependency on this value at all. Same '
            'out-of-scope category as "proc chances" (docs/potency-system.md\'s "Out of scope by design").',
        ),
    ],
    spell_icon_id=2109,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Cheat Death": effects unchanged (eff0 aura 69 SCHOOL_ABSORB, the chance '
        "33/66/100 in CalcValue); tooltip = the doc's; rebound to spell_rog_cheat_death_rework below. The 15% is "
        'CHEAT_DEATH_CAP_MAX_HEALTH_PCT in rogue_subtlety.py.'
    ),
    raw_overrides={
        'AttributesEx3': 524288,
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': _with_cap('You have a $s1% chance to absorb an attack that would otherwise kill you, as long as it is no larger than your current health plus ' + _c(CHEAT_DEATH_CAP_MAX_HEALTH_PCT) + '% of your maximum health, and all damage you take is reduced by $45182s1% for $45182d. Shares a 2 min cooldown with Ardent Defender and Spirit of Redemption.', 'Capstone: Cheating death also resets your Vanish.', False),
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassMask_2': 1024,
        'SpellClassSet': 8,
        'SpellLevel': 1,
        'SpellPriority': 50,
    },
)


cheat_death_31229 = spell(
    id=31229,
    name='Cheat Death',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(
            type=EffectType.APPLY_AURA, base_points=65, implicit_target_a=1, apply_aura=69, misc_value=127,
            potency_excluded='not a damage/absorb value - same as 31228, this effect\'s own CalcValue() is '
            'read as a proc-chance percent by spell_rog_cheat_death::CalculateAmount, not a shield size.',
        ),
    ],
    spell_icon_id=2109,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Cheat Death": effects unchanged (eff0 aura 69 SCHOOL_ABSORB, the chance '
        "33/66/100 in CalcValue); tooltip = the doc's; rebound to spell_rog_cheat_death_rework below. The 15% is "
        'CHEAT_DEATH_CAP_MAX_HEALTH_PCT in rogue_subtlety.py.'
    ),
    raw_overrides={
        'AttributesEx3': 524288,
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': _with_cap('You have a $s1% chance to absorb an attack that would otherwise kill you, as long as it is no larger than your current health plus ' + _c(CHEAT_DEATH_CAP_MAX_HEALTH_PCT) + '% of your maximum health, and all damage you take is reduced by $45182s1% for $45182d. Shares a 2 min cooldown with Ardent Defender and Spirit of Redemption.', 'Capstone: Cheating death also resets your Vanish.', False),
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassMask_2': 1024,
        'SpellClassSet': 8,
        'SpellLevel': 1,
        'SpellPriority': 50,
    },
)


cheat_death_31230 = spell(
    id=31230,
    name='Cheat Death',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(
            type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=69, misc_value=127,
            potency_excluded='not a damage/absorb value - same as 31228, this effect\'s own CalcValue() is '
            'read as a proc-chance percent by spell_rog_cheat_death::CalculateAmount, not a shield size.',
        ),
    ],
    spell_icon_id=2109,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Cheat Death": effects unchanged (eff0 aura 69 SCHOOL_ABSORB, the chance '
        "33/66/100 in CalcValue); tooltip = the doc's; rebound to spell_rog_cheat_death_rework below. The 15% is "
        'CHEAT_DEATH_CAP_MAX_HEALTH_PCT in rogue_subtlety.py.'
    ),
    raw_overrides={
        'AttributesEx3': 524288,
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': _with_cap('You have a $s1% chance to absorb an attack that would otherwise kill you, as long as it is no larger than your current health plus ' + _c(CHEAT_DEATH_CAP_MAX_HEALTH_PCT) + '% of your maximum health, and all damage you take is reduced by $45182s1% for $45182d. Shares a 2 min cooldown with Ardent Defender and Spirit of Redemption.', 'Capstone: Cheating death also resets your Vanish.', True),
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassMask_2': 1024,
        'SpellClassSet': 8,
        'SpellLevel': 1,
        'SpellPriority': 50,
    },
)


find_weakness_31234 = spell(
    id=31234,
    name='Find Weakness',
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
    spell_icon_id=2112,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Find Weakness": one flat CRITICAL_CHANCE +2/4/6 on FIND_WEAKNESS_READ (Garrote, Fan of Knives, Riposte, every poison, the finisher / single-strike / Mutilate-hand / Kingsbane-hand / Kingsbane-DoT groups); the stock pct DAMAGE / DOT effects are gone.'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712190,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Critical strike chance of your Rogue abilities and Rogue poisons increased by $s1%.',
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **m.read_mask_keys(0, m.FIND_WEAKNESS_READ_S3),
    },
)


find_weakness_31235 = spell(
    id=31235,
    name='Find Weakness',
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
    spell_icon_id=2112,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Find Weakness": one flat CRITICAL_CHANCE +2/4/6 on FIND_WEAKNESS_READ (Garrote, Fan of Knives, Riposte, every poison, the finisher / single-strike / Mutilate-hand / Kingsbane-hand / Kingsbane-DoT groups); the stock pct DAMAGE / DOT effects are gone.'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712190,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Critical strike chance of your Rogue abilities and Rogue poisons increased by $s1%.',
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **m.read_mask_keys(0, m.FIND_WEAKNESS_READ_S3),
    },
)


find_weakness_31236 = spell(
    id=31236,
    name='Find Weakness',
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
    ],
    spell_icon_id=2112,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Find Weakness": one flat CRITICAL_CHANCE +2/4/6 on FIND_WEAKNESS_READ (Garrote, Fan of Knives, Riposte, every poison, the finisher / single-strike / Mutilate-hand / Kingsbane-hand / Kingsbane-DoT groups); the stock pct DAMAGE / DOT effects are gone.'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712190,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Critical strike chance of your Rogue abilities and Rogue poisons increased by $s1%.',
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **m.read_mask_keys(0, m.FIND_WEAKNESS_READ_S3),
    },
)


quick_recovery_31244 = spell(
    id=31244,
    name='Quick Recovery',
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
    spell_icon_id=2116,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Quick Recovery": eff0 DUMMY 15/30 = the Mutilate refund chance (Rogue::ResolveDualStrike reads it); the healing aura and the failed-finisher proc are gone. ProcTypeMask 0 / ProcChance 101 (R8). The 10 energy is RogueData::QUICK_RECOVERY_ENERGY cast through stock 31663.'
    ),
    raw_overrides={
        'AttributesEx3': 524288,
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Your Mutilate has a $s1% chance to refund 10 energy.',
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'ProcTypeMask': 0,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        'SpellLevel': 1,
        'SpellPriority': 50,
    },
)


quick_recovery_31245 = spell(
    id=31245,
    name='Quick Recovery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2116,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Quick Recovery": eff0 DUMMY 15/30 = the Mutilate refund chance (Rogue::ResolveDualStrike reads it); the healing aura and the failed-finisher proc are gone. ProcTypeMask 0 / ProcChance 101 (R8). The 10 energy is RogueData::QUICK_RECOVERY_ENERGY cast through stock 31663.'
    ),
    raw_overrides={
        'AttributesEx3': 524288,
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Your Mutilate has a $s1% chance to refund 10 energy.',
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'ProcTypeMask': 0,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        'SpellLevel': 1,
        'SpellPriority': 50,
    },
)


deadened_nerves_31380 = spell(
    id=31380,
    name='Deadened Nerves',
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
    ],
    spell_icon_id=2110,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces all damage taken by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellLevel': 1, 'SpellPriority': 50},
)


deadened_nerves_31382 = spell(
    id=31382,
    name='Deadened Nerves',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
    ],
    spell_icon_id=2110,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces all damage taken by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellLevel': 1, 'SpellPriority': 50},
)


deadened_nerves_31383 = spell(
    id=31383,
    name='Deadened Nerves',
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
    ],
    spell_icon_id=2110,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces all damage taken by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellLevel': 1, 'SpellPriority': 50},
)


surprise_attacks_32601 = spell(
    id=32601,
    name='Surprise Attacks',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=108, misc_value=0),
    ],
    spell_icon_id=2119,
    notes=(
        'rogue-rework S3a A2, Combat doc "Surprise Attacks": eff0 pct DAMAGE +2 on SURPRISE_ATTACKS_READ (stale A_1 / A_2 rewritten); the stock aura 202 (finishers cannot be dodged) and eff1 pct DAMAGE are gone (stale B_1 0x2200000e cleared). Ranks 2 / 3 are 203981 / 203982 (rogue_combat.py); the capstone chance is 203982 eff1 ($203982s2).'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': _with_cap('Increases the damage dealt by your Sinister Strike, Pistol Shot, Eviscerate, Between the Eyes, Backstab, Ambush and Shiv by $s1%.', 'Capstone: When your Sinister Strike strikes an additional time, you have a $203982s2% chance that your next Pistol Shot fires ' + _c(SURPRISE_ATTACKS_EXTRA_SHOTS) + ' additional times.', False),
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        'ProcTypeMask': 0,
        'NameSubtext_Lang_enUS': 'Rank 1',
        **m.read_mask_keys(0, m.SURPRISE_ATTACKS_READ),
        **m.clear_mask_keys(1, 2),
    },
)


combat_potency_35541 = spell(
    id=35541,
    name='Combat Potency',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=35542),
    ],
    spell_icon_id=2260,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your successful off-hand melee attacks a $h% chance to generate $35542s1 Energy.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'ProcTypeMask': 4, 'RangeIndex': 1, 'SpellClassSet': 8},
)


combat_potency_35550 = spell(
    id=35550,
    name='Combat Potency',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=35545),
    ],
    spell_icon_id=2260,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your successful off-hand melee attacks a $h% chance to generate $35545s1 Energy.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'ProcTypeMask': 4, 'RangeIndex': 1, 'SpellClassSet': 8},
)


combat_potency_35551 = spell(
    id=35551,
    name='Combat Potency',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=35546),
    ],
    spell_icon_id=2260,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your successful off-hand melee attacks a $h% chance to generate $35546s1 Energy.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'ProcTypeMask': 4, 'RangeIndex': 1, 'SpellClassSet': 8},
)


combat_potency_35552 = spell(
    id=35552,
    name='Combat Potency',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=35547),
    ],
    spell_icon_id=2260,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your successful off-hand melee attacks a $h% chance to generate $35547s1 Energy.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'ProcTypeMask': 4, 'RangeIndex': 1, 'SpellClassSet': 8},
)


combat_potency_35553 = spell(
    id=35553,
    name='Combat Potency',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=35548),
    ],
    spell_icon_id=2260,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives your successful off-hand melee attacks a $h% chance to generate $35548s1 Energy.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'ProcTypeMask': 4, 'RangeIndex': 1, 'SpellClassSet': 8},
)


deadly_brew_51625 = spell(
    id=51625,
    name='Deadly Brew',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2963,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Deadly Brew": eff0 DUMMY 50/100 = the chance Rogue::ApplyPoison reads (x Proc Chance, 4 s per-rogue ICD, RogueData::DEADLY_BREW_ICD_MS); the stock mask / misc 18 / proc flags are gone (ProcTypeMask 0, ProcChance 101, R8) so no default proc entry appears once -51625 is removed.'
    ),
    raw_overrides={
        'AttributesEx3': 67108864,
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'When you apply Instant, Deadly or Mind-Numbing poison to a target, you have a $s1% chance to apply Crippling poison. This effect can only occur once every 4 sec.',
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'ProcTypeMask': 0,
        'RangeIndex': 1,
        'SpellClassSet': 8,
    },
)


deadly_brew_51626 = spell(
    id=51626,
    name='Deadly Brew',
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
    ],
    spell_icon_id=2963,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Deadly Brew": eff0 DUMMY 50/100 = the chance Rogue::ApplyPoison reads (x Proc Chance, 4 s per-rogue ICD, RogueData::DEADLY_BREW_ICD_MS); the stock mask / misc 18 / proc flags are gone (ProcTypeMask 0, ProcChance 101, R8) so no default proc entry appears once -51625 is removed.'
    ),
    raw_overrides={
        'AttributesEx3': 67108864,
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'When you apply Instant, Deadly or Mind-Numbing poison to a target, you have a $s1% chance to apply Crippling poison. This effect can only occur once every 4 sec.',
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'ProcTypeMask': 0,
        'RangeIndex': 1,
        'SpellClassSet': 8,
    },
)


blood_spatter_51632 = spell(
    id=51632,
    name='Blood Spatter',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=2957,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage caused by your Garrote and Rupture abilities by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1048832, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)


blood_spatter_51633 = spell(
    id=51633,
    name='Blood Spatter',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=2957,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage caused by your Garrote and Rupture abilities by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1048832, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)


cut_to_the_chase_51664 = spell(
    id=51664,
    name='Cut to the Chase',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=22),
    ],
    spell_icon_id=2909,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Eviscerate and Envenom abilities have a $h% chance to refresh your Slice and Dice duration to its 5 combo point maximum.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1048832, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellVisualID_1': 11819},
)


cut_to_the_chase_51665 = spell(
    id=51665,
    name='Cut to the Chase',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=22),
    ],
    spell_icon_id=2909,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Eviscerate and Envenom abilities have a $h% chance to refresh your Slice and Dice duration to its 5 combo point maximum.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1048832, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 40, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellVisualID_1': 11819},
)


cut_to_the_chase_51667 = spell(
    id=51667,
    name='Cut to the Chase',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=22),
    ],
    spell_icon_id=2909,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Eviscerate and Envenom abilities have a $h% chance to refresh your Slice and Dice duration to its 5 combo point maximum.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1048832, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 60, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellVisualID_1': 11819},
)


cut_to_the_chase_51668 = spell(
    id=51668,
    name='Cut to the Chase',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=22),
    ],
    spell_icon_id=2909,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Eviscerate and Envenom abilities have a $h% chance to refresh your Slice and Dice duration to its 5 combo point maximum.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1048832, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 80, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellVisualID_1': 11819},
)


cut_to_the_chase_51669 = spell(
    id=51669,
    name='Cut to the Chase',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=22),
    ],
    spell_icon_id=2909,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Eviscerate and Envenom abilities have a $h% chance to refresh your Slice and Dice duration to its 5 combo point maximum.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1048832, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellVisualID_1': 11819},
)


throwing_specialization_51679 = spell(
    id=51679,
    name='Throwing Specialization',
    school=School.NORMAL,
    attributes=262352,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER),
    ],
    spell_icon_id=2910,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Throwing Specialization": eff0 pct DAMAGE +20 on THROWING_SPEC_READ '
        '(Deadly Throw d1 b0, Fan of Knives d1 b18: 51723, 52874, the Second Volley copies and the Deadly Throw copy '
        '204168); the stock RANGE modifier and the interrupt proc (51680) are gone, raw ProcTypeMask 0 / ProcChance '
        '101 with the -5952 / 32748 spell_proc rows removed below. The capstone (51679 held) is read by '
        "spell_rog_deadly_throw_subtlety. The copy 204168 carries d1 b0 only, so an Assassination hybrid's "
        'Ruthlessness / Find Weakness on finishers do not reach the copies (R21).'
    ),
    raw_overrides={
        'AttributesEx3': 67108864,
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': _with_cap('Increases the damage of your Deadly Throw and Fan of Knives by $s1%.', f'Capstone: Your Deadly Throw also strikes up to {_c(THROWING_SPEC_EXTRA_TARGETS)} additional enemies near the target.', True),
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'ProcTypeMask': 0,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **m.read_mask_keys(0, m.THROWING_SPEC_READ),
        **m.clear_mask_keys(1),
    },
)


savage_combat_51682 = spell(
    id=51682,
    name='Savage Combat',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=127, trigger_spell=58684),
    ],
    spell_icon_id=1959,
    notes=(
        'rogue-rework S3a A2, Combat doc "Savage Combat": eff1 aura 166 (+attack power) removed (C4); eff0 -> 58684 and the stock row -51682 / spell_rog_savage_combat on 58683 / 58684 stay. Stale B_1 0x400000 cleared (R8).'
    ),
    raw_overrides={
        'AttributesEx3': 67108864,
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Enemies you have poisoned take $58684s1% more Physical damage.',
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EffectSpellClassMaskA_1': 4194304,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 100,
        'ProcTypeMask': 69632,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **m.clear_mask_keys(1, 2),
    },
)


waylay_51692 = spell(
    id=51692,
    name='Waylay',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER),
    ],
    spell_icon_id=2958,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Waylay": eff0 pct DAMAGE +10 on Ambush (WAYLAY_READ); the stock slow proc'
        ' is gone (raw ProcTypeMask 0 / ProcChance 101, spell_proc -51692 removed below); the junk eff1 (bp -1, B_1 '
        '0x2000004) zeroed.'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': _with_cap('Increases the damage of your Ambush by $s1%.', 'Capstone: Your Ambush unbalances the target, increasing the time between its melee and ranged attacks by $51693s1% and reducing its movement speed by $51693s2% for $51693d.', False),
        'EffectBasePoints_2': 0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EffectDieSides_2': 0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'ProcTypeMask': 0,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **m.read_mask_keys(0, m.WAYLAY_READ),
        **m.clear_mask_keys(1),
    },
)


waylay_51696 = spell(
    id=51696,
    name='Waylay',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=51693),
    ],
    spell_icon_id=2958,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Waylay": eff0 pct DAMAGE +20 on Ambush (WAYLAY_READ); eff1 aura 42 -> '
        '51693 (the stock slow, the capstone). Raw ProcTypeMask 16 / ProcChance 100 kept for the spell_proc 51696 row'
        ' below (family mask WAYLAY_READ, phase HIT, chance 100, C1).'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': _with_cap('Increases the damage of your Ambush by $s1%.', 'Capstone: Your Ambush unbalances the target, increasing the time between its melee and ranged attacks by $51693s1% and reducing its movement speed by $51693s2% for $51693d.', True),
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 100,
        'ProcTypeMask': 16,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **m.read_mask_keys(0, m.WAYLAY_READ),
        **m.clear_mask_keys(1),
    },
)


slaughter_from_the_shadows_51708 = spell(
    id=51708,
    name='Slaughter from the Shadows',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER),
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2962,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Slaughter from the Shadows": eff0 pct DAMAGE +5 on Backstab '
        '(SLAUGHTER_READ d0 b2), eff1 hidden DUMMY 33 (the % chance to take SLAUGHTER_CDR_MS off Shadow Dance; read '
        'by Rogue::OnBackstabHit). The stock COST modifiers and aura 79 are gone (no rogue effect may lower a cost). '
        'The 0.5 sec in the text is the SLAUGHTER_CDR_MS const in rogue_subtlety.py.'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the damage of your Backstab by $s1%. Your Backstab has a $s2% chance to reduce the remaining cooldown of Shadow Dance by ' + _sec(SLAUGHTER_CDR_MS) + ' sec.',
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **m.read_mask_keys(0, m.SLAUGHTER_READ),
        **m.clear_mask_keys(1, 2),
    },
)


slaughter_from_the_shadows_51709 = spell(
    id=51709,
    name='Slaughter from the Shadows',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER),
        Effect(type=EffectType.APPLY_AURA, base_points=65, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2962,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Slaughter from the Shadows": eff0 pct DAMAGE +10 on Backstab '
        '(SLAUGHTER_READ d0 b2), eff1 hidden DUMMY 66 (the % chance to take SLAUGHTER_CDR_MS off Shadow Dance; read '
        'by Rogue::OnBackstabHit). The stock COST modifiers and aura 79 are gone (no rogue effect may lower a cost). '
        'The 0.5 sec in the text is the SLAUGHTER_CDR_MS const in rogue_subtlety.py.'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the damage of your Backstab by $s1%. Your Backstab has a $s2% chance to reduce the remaining cooldown of Shadow Dance by ' + _sec(SLAUGHTER_CDR_MS) + ' sec.',
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **m.read_mask_keys(0, m.SLAUGHTER_READ),
        **m.clear_mask_keys(1, 2),
    },
)


slaughter_from_the_shadows_51710 = spell(
    id=51710,
    name='Slaughter from the Shadows',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2962,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Slaughter from the Shadows": eff0 pct DAMAGE +15 on Backstab '
        '(SLAUGHTER_READ d0 b2), eff1 hidden DUMMY 100 (the % chance to take SLAUGHTER_CDR_MS off Shadow Dance; read '
        'by Rogue::OnBackstabHit). The stock COST modifiers and aura 79 are gone (no rogue effect may lower a cost). '
        'The 0.5 sec in the text is the SLAUGHTER_CDR_MS const in rogue_subtlety.py.'
    ),
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the damage of your Backstab by $s1%. Your Backstab has a $s2% chance to reduce the remaining cooldown of Shadow Dance by ' + _sec(SLAUGHTER_CDR_MS) + ' sec.',
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **m.read_mask_keys(0, m.SLAUGHTER_READ),
        **m.clear_mask_keys(1, 2),
    },
)


slaughter_from_the_shadows_51711 = spell(
    id=51711,
    name='Slaughter from the Shadows',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-17, implicit_target_a=1, apply_aura=107, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=107, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=79, misc_value=127),
    ],
    spell_icon_id=2962,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the energy cost of your Backstab and Ambush abilities by $s1 and the energy cost of your Hemorrhage by $s2, and increases all damage done by $s3%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 516, 'EffectSpellClassMaskB_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)


slaughter_from_the_shadows_51712 = spell(
    id=51712,
    name='Slaughter from the Shadows',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=107, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=-6, implicit_target_a=1, apply_aura=107, misc_value=14),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=79, misc_value=127),
    ],
    spell_icon_id=2962,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the energy cost of your Backstab and Ambush abilities by $s1 and the energy cost of your Hemorrhage by $s2, and increases all damage done by $s3%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 516, 'EffectSpellClassMaskB_1': 33554432, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)


master_poisoner_58410 = spell(
    id=58410,
    name='Master Poisoner',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=231, misc_value=23, trigger_spell=45176),
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=246, misc_value=4),
    ],
    spell_icon_id=1960,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Master Poisoner": eff0 (aura 231 -> 45176, crit 1/2/3) and the raw EffectBasePoints_3 / EffectDieSides_3 (Envenom keep chance 33/66/100, read by SpellEffects.cpp:589-593 off Effects[2]) are stock and load-bearing (R6); icon 1960 and the 231 / 246 effect order unchanged. eff1 aura 246 misc 4 rewritten -17/34/50 -> -10/20/30. Rank 3 (58410) is the capstone: Rogue::GetLethalSlots returns 2 while it is held.'
    ),
    raw_overrides={
        'AttributesEx3': 67108864,
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases the critical strike chance of all spells and attacks made against any target you have poisoned by $s1%, reduces the duration of all Poison effects applied to you by $s2%, and gives Envenom a $s3% chance not to consume Deadly Poison. Does not stack with other similar effects.\n\nCapstone: You may have two Lethal poisons active at once.',
        'EffectBasePoints_3': 99,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EffectDieSides_3': 1,
        'EffectSpellClassMaskA_2': 524288,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 100,
        'ProcTypeMask': 69632,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        'SpellLevel': 1,
        'SpellPriority': 50,
    },
)


savage_combat_58413 = spell(
    id=58413,
    name='Savage Combat',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=127, trigger_spell=58683),
    ],
    spell_icon_id=1959,
    notes=(
        'rogue-rework S3a A2, Combat doc "Savage Combat": eff1 aura 166 (+attack power) removed (C4); eff0 -> 58683 and the stock row -51682 / spell_rog_savage_combat on 58683 / 58684 stay. Stale B_1 0x400000 cleared (R8).'
    ),
    raw_overrides={
        'AttributesEx3': 67108864,
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Enemies you have poisoned take $58683s1% more Physical damage.',
        'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EffectSpellClassMaskA_1': 4194304,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 100,
        'ProcTypeMask': 69632,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **m.clear_mask_keys(1, 2),
    },
)


filthy_tricks_58414 = spell(
    id=58414,
    name='Filthy Tricks',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-90001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=-6, implicit_target_a=1, apply_aura=107, misc_value=14),
    ],
    spell_icon_id=2906,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown by $/1000;s1 sec and energy cost by $s3 of your Tricks of the Trade, Distract and Shadowstep abilities and reduces the cooldown of Preparation by $/60000;S2 min.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_3': 8, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskA_2': 131584, 'EffectSpellClassMaskB_2': 4096, 'EffectSpellClassMaskC_1': 4096, 'EffectSpellClassMaskC_2': 131584, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellVisualID_1': 11826},
)


filthy_tricks_58415 = spell(
    id=58415,
    name='Filthy Tricks',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-180001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=107, misc_value=14),
    ],
    spell_icon_id=2906,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown by $/1000;s1 sec and energy cost by $s3 of your Tricks of the Trade, Distract and Shadowstep abilities and reduces the cooldown of Preparation by $/60000;S2 min.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_3': 8, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskA_2': 131584, 'EffectSpellClassMaskB_2': 4096, 'EffectSpellClassMaskC_1': 4096, 'EffectSpellClassMaskC_2': 131584, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8, 'SpellVisualID_1': 11826},
)


relentless_strikes_58422 = spell(
    id=58422,
    name='Relentless Strikes',
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
    spell_icon_id=559,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Relentless Strikes": eff0 hidden DUMMY 20 (the % chance per combo point; '
        'read by GetRankAmount EFFECT_0). The stock aura 109 -> 14181 is gone (the dispatcher rolls it and casts '
        '14181 + 204155); stale A_1 0x3E0000 / A_2 9 cleared; EffectPointsPerCombo_1 zeroed (SpellInfo::CalcValue '
        "adds PointsPerComboPoint x the caster's combo points to a DUMMY value)."
    ),
    raw_overrides={
        'AttributesEx': 1048576,
        'AttributesEx4': 2,
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': "Your finishing moves have a $s1% chance per combo point to restore $14181s1 energy and to cause your attacks to ignore $204155s1% of your target's armor for $204155d.",
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EffectPointsPerCombo_1': 0.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **m.clear_mask_keys(0),
    },
)


relentless_strikes_58423 = spell(
    id=58423,
    name='Relentless Strikes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=559,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Relentless Strikes": eff0 hidden DUMMY 30 (the % chance per combo point; '
        'read by GetRankAmount EFFECT_0). The stock aura 109 -> 14181 is gone (the dispatcher rolls it and casts '
        '14181 + 204155); stale A_1 0x3E0000 / A_2 9 cleared; EffectPointsPerCombo_1 zeroed (SpellInfo::CalcValue '
        "adds PointsPerComboPoint x the caster's combo points to a DUMMY value)."
    ),
    raw_overrides={
        'AttributesEx': 1048576,
        'AttributesEx4': 2,
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': "Your finishing moves have a $s1% chance per combo point to restore $14181s1 energy and to cause your attacks to ignore $204155s1% of your target's armor for $204155d.",
        'EffectBonusMultiplier_1': 1.0,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EffectPointsPerCombo_1': 0.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': 8,
        **m.clear_mask_keys(0),
    },
)


relentless_strikes_58424 = spell(
    id=58424,
    name='Relentless Strikes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=109, trigger_spell=14181),
    ],
    spell_icon_id=559,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 1048576, 'AttributesEx4': 2, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your finishing moves have a $b1% chance per combo point to restore $14181s1 energy.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectPointsPerCombo_1': 16.0, 'EffectSpellClassMaskA_1': 4063232, 'EffectSpellClassMaskA_2': 9, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)


relentless_strikes_58425 = spell(
    id=58425,
    name='Relentless Strikes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=109, trigger_spell=14181),
    ],
    spell_icon_id=559,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 1048576, 'AttributesEx4': 2, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your finishing moves have a $b1% chance per combo point to restore $14181s1 energy.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectPointsPerCombo_1': 20.0, 'EffectSpellClassMaskA_1': 4063232, 'EffectSpellClassMaskA_2': 9, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)


aggression_61330 = spell(
    id=61330,
    name='Aggression',
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
    ],
    spell_icon_id=84,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Sinister Strike, Backstab, and Eviscerate abilities by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 131078, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)


aggression_61331 = spell(
    id=61331,
    name='Aggression',
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
    ],
    spell_icon_id=84,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Sinister Strike, Backstab, and Eviscerate abilities by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 131078, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 8},
)


crippling_poison_3409 = spell(
    id=3409,
    name='Crippling Poison',
    school=School.NATURE,
    dispel=DispelType.POISON,
    mechanic=11,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=6, apply_aura=AuraType.MOD_DECREASE_SPEED),
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=197),
    ],
    spell_icon_id=163,
    notes=(
        'pulled from source/spells/npc.csv (rogue-rework RG0a). Payload of the 203704 Crippling Poison self aura: '
        'slow -50% (stored -51; stock -70%), 12 s; icon 163 kept (it is the diminishing-returns key, SpellMgr.cpp '
        '~199-215); range 100 (script-cast payload, range-checked even when triggered); EquippedItemClass -1; '
        'identity bit d0 b14 + poison group d1 b19 (no damage SpellMod reads the group on this row).'
    ),
    raw_overrides={'AttributesEx': 131208, 'AttributesEx2': 16777220, 'AttributesEx4': 2048, 'CastingTimeIndex': 1, 'ProcTypeMask': 32768, 'ProcChance': 100, 'BaseLevel': 20, 'SpellLevel': 20, 'EquippedItemClass': -1, 'SpellVisualID_1': 5100, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces the target's movement speed by $3409s1% for $3409d.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement slowed.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 8, 'SpellClassMask_1': m.CRIPPLING_POISON, 'SpellClassMask_2': m.POISON_GROUP, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


mind_numbing_poison_5760 = spell(
    id=5760,
    name='Mind-numbing Poison',
    school=School.NATURE,
    dispel=DispelType.POISON,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=6, apply_aura=216),
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=197),
    ],
    spell_icon_id=264,
    notes=(
        'pulled from source/spells/npc.csv (rogue-rework RG0a). Payload of the 203705 Mind-numbing Poison self aura: '
        'aura 216 (casting speed) stored -51 = casting time x1.5 (stock -31, +30%), 10 s; the id is kept (Shade of '
        'Aran\'s immunity list keys it); range 100; EquippedItemClass -1; identity bit d0 b15 + poison group d1 b19.'
    ),
    raw_overrides={'AttributesEx': 136, 'AttributesEx2': 16777216, 'AttributesEx3': 131072, 'CastingTimeIndex': 1, 'ProcTypeMask': 32768, 'ProcChance': 100, 'BaseLevel': 24, 'SpellLevel': 24, 'EquippedItemClass': -1, 'SpellVisualID_1': 5100, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the target's casting time by $5760s1% for $5760d.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Casting time increased.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 8, 'SpellClassMask_1': m.MIND_NUMBING_POISON, 'SpellClassMask_2': m.POISON_GROUP, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


# rogue-rework RG0a (WP-R M1): Wound Poison no longer cuts healing, so it leaves stock group 1061 "Healing Taken
# Debuffs" (rule 4, exclusive-highest; Mortal Strike, Aimed Shot, Furious Attacks) via nested subgroup 1057. It stays in
# 1058 "Poisons". AttributesEx3 0x80 (stack per caster, m2): a second rogue's Wound does not replace this rogue's.
leave_spell_group(1061, -1057)


# ---- rogue-rework S1a WP-0.2: stock-only Assassination rank spells pulled unedited (pull_dsl.py --constants) ----
# Malice 14138-14140, Remorseless Attacks 14144 / 14148, Fleet Footed 31208 / 31209, Focused Attacks 51634-51636 and its
# energize 51637. Untouched reference copies (generate.py skips them) until A2 rewrites them in place per the S1a WP-BRIEF.
malice_14138 = spell(
    id=14138,
    name='Malice',
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
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_CUSTOM_STAT_PCT, misc_value=1 << 11),
    ],
    spell_icon_id=86,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Malice": stock crit aura (52) rewritten to aura 306 MOD_CUSTOM_STAT_PCT misc 1 << 11 (CR_PROC_CHANCE, Unit.h), stored amount = percent - 1 (the Volatility 200960 / Crimson Resolve shape): +2/4/6% Proc Chance. Ranks 14141 / 14142 stay stock and leave the talent (A1). No family bits.'
    ),
    raw_overrides={
        'CastingTimeIndex': 1,
        'ProcChance': 101,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases your Proc Chance by $s1%.',
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectBonusMultiplier_1': 1.0,
    },
)


malice_14139 = spell(
    id=14139,
    name='Malice',
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
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.MOD_CUSTOM_STAT_PCT, misc_value=1 << 11),
    ],
    spell_icon_id=86,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Malice": stock crit aura (52) rewritten to aura 306 MOD_CUSTOM_STAT_PCT misc 1 << 11 (CR_PROC_CHANCE, Unit.h), stored amount = percent - 1 (the Volatility 200960 / Crimson Resolve shape): +2/4/6% Proc Chance. Ranks 14141 / 14142 stay stock and leave the talent (A1). No family bits.'
    ),
    raw_overrides={
        'CastingTimeIndex': 1,
        'ProcChance': 101,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases your Proc Chance by $s1%.',
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectBonusMultiplier_1': 1.0,
    },
)


malice_14140 = spell(
    id=14140,
    name='Malice',
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
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.MOD_CUSTOM_STAT_PCT, misc_value=1 << 11),
    ],
    spell_icon_id=86,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Malice": stock crit aura (52) rewritten to aura 306 MOD_CUSTOM_STAT_PCT misc 1 << 11 (CR_PROC_CHANCE, Unit.h), stored amount = percent - 1 (the Volatility 200960 / Crimson Resolve shape): +2/4/6% Proc Chance. Ranks 14141 / 14142 stay stock and leave the talent (A1). No family bits.'
    ),
    raw_overrides={
        'CastingTimeIndex': 1,
        'ProcChance': 101,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases your Proc Chance by $s1%.',
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectBonusMultiplier_1': 1.0,
    },
)


remorseless_attacks_14144 = spell(
    id=14144,
    name='Remorseless Attacks',
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
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=695,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Remorseless Attacks": hidden rank marker: eff0 DUMMY 25/50 (the crit amount Rogue::OnBleedVictimDied passes as bp0 to the crit buff 203838), no trigger spell, ProcTypeMask 0 and ProcChance 101 (R8/R12: a DUMMY rank with DBC proc flags would get a default proc entry once the -14143 chain is unbound). Rank 2 also casts the capstone buff 203839 (C++: HasAura(14148)).'
    ),
    raw_overrides={
        'CastingTimeIndex': 1,
        'ProcTypeMask': 0,
        'ProcChance': 101,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'When an enemy afflicted by one of your bleeds dies, your next Sinister Strike, Backstab, Mutilate, Ambush, or Ghostly Strike has a $s1% increased critical strike chance. Lasts $203838d.\n\n|cFF9D9D9DCapstone: Triggering Remorseless Attacks also increases your poison damage by $203839s1% for $203839d.|r',
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
    },
)


remorseless_attacks_14148 = spell(
    id=14148,
    name='Remorseless Attacks',
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
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=695,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Remorseless Attacks": hidden rank marker: eff0 DUMMY 25/50 (the crit amount Rogue::OnBleedVictimDied passes as bp0 to the crit buff 203838), no trigger spell, ProcTypeMask 0 and ProcChance 101 (R8/R12: a DUMMY rank with DBC proc flags would get a default proc entry once the -14143 chain is unbound). Rank 2 also casts the capstone buff 203839 (C++: HasAura(14148)).'
    ),
    raw_overrides={
        'CastingTimeIndex': 1,
        'ProcTypeMask': 0,
        'ProcChance': 101,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'When an enemy afflicted by one of your bleeds dies, your next Sinister Strike, Backstab, Mutilate, Ambush, or Ghostly Strike has a $s1% increased critical strike chance. Lasts $203838d.\n\nCapstone: Triggering Remorseless Attacks also increases your poison damage by $203839s1% for $203839d.',
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
    },
)


fleet_footed_31208 = spell(
    id=31208,
    name='Fleet Footed',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MOD_MOUNTED_SPEED_NOT_STACK),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2113,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Fleet Footed": eff0 aura 172 MOD_MOUNTED_SPEED_NOT_STACK +3/6%, eff1 DUMMY 10 (% per combo point at every rank; Rogue::OnSpellCast reads it). The stock movement-impairing duration aura and the run-speed aura are gone. Rank 3 is 203824 (+10, A3).'
    ),
    raw_overrides={
        'CastingTimeIndex': 1,
        'ProcChance': 101,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases your mounted movement speed by $s1%. This does not stack with other movement speed increasing effects. Your finishing moves have a $s2% chance per combo point to clear any movement speed reduction and immobilization effects.',
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
    },
)


fleet_footed_31209 = spell(
    id=31209,
    name='Fleet Footed',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.MOD_MOUNTED_SPEED_NOT_STACK),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2113,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Fleet Footed": eff0 aura 172 MOD_MOUNTED_SPEED_NOT_STACK +3/6%, eff1 DUMMY 10 (% per combo point at every rank; Rogue::OnSpellCast reads it). The stock movement-impairing duration aura and the run-speed aura are gone. Rank 3 is 203824 (+10, A3).'
    ),
    raw_overrides={
        'CastingTimeIndex': 1,
        'ProcChance': 101,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases your mounted movement speed by $s1%. This does not stack with other movement speed increasing effects. Your finishing moves have a $s2% chance per combo point to clear any movement speed reduction and immobilization effects.',
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
    },
)


focused_attacks_51634 = spell(
    id=51634,
    name='Focused Attacks',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=22, trigger_spell=51637),
    ],
    spell_icon_id=2982,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Focused Attacks": ProcChance 33/66/100 and the proc shape are stock (the CheckProc fork spell_rog_focused_attacks_rework rejects the Mutilate / Kingsbane hands and Fan of Knives, which resolve once per cast in C++); the energy amount lives in 51637 (token $51637s1).'
    ),
    raw_overrides={
        'CastingTimeIndex': 1,
        'ProcTypeMask': 20,
        'ProcChance': 33,
        'DurationIndex': 0,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'EffectSpellClassMaskA_1': 1048832,
        'SpellVisualID_1': 11818,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Your melee critical strikes have a $h% chance to give you $51637s1 energy.',
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
    },
)


focused_attacks_51635 = spell(
    id=51635,
    name='Focused Attacks',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=22, trigger_spell=51637),
    ],
    spell_icon_id=2982,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Focused Attacks": ProcChance 33/66/100 and the proc shape are stock (the CheckProc fork spell_rog_focused_attacks_rework rejects the Mutilate / Kingsbane hands and Fan of Knives, which resolve once per cast in C++); the energy amount lives in 51637 (token $51637s1).'
    ),
    raw_overrides={
        'CastingTimeIndex': 1,
        'ProcTypeMask': 20,
        'ProcChance': 66,
        'DurationIndex': 0,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'EffectSpellClassMaskA_1': 1048832,
        'SpellVisualID_1': 11818,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Your melee critical strikes have a $h% chance to give you $51637s1 energy.',
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
    },
)


focused_attacks_51636 = spell(
    id=51636,
    name='Focused Attacks',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=22, trigger_spell=51637),
    ],
    spell_icon_id=2982,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Focused Attacks": ProcChance 33/66/100 and the proc shape are stock (the CheckProc fork spell_rog_focused_attacks_rework rejects the Mutilate / Kingsbane hands and Fan of Knives, which resolve once per cast in C++); the energy amount lives in 51637 (token $51637s1).'
    ),
    raw_overrides={
        'CastingTimeIndex': 1,
        'ProcTypeMask': 20,
        'ProcChance': 100,
        'DurationIndex': 0,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'EffectSpellClassMaskA_1': 1048832,
        'SpellVisualID_1': 11818,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Your melee critical strikes have a $h% chance to give you $51637s1 energy.',
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
    },
)


focused_attacks_energize_51637 = spell(
    id=51637,
    name='Focused Attacks',
    school=School.NORMAL,
    attributes=16,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.ENERGIZE, base_points=2, implicit_target_a=1, misc_value=3),
    ],
    spell_icon_id=2982,
    notes=(
        'rogue-rework S1a A2, Assassination doc "Focused Attacks": ENERGIZE misc 3 (energy) bp 2 = 3 energy (stock 2).'
    ),
    raw_overrides={
        'CastingTimeIndex': 1,
        'ProcChance': 101,
        'DurationIndex': 0,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'EffectSpellClassMaskA_1': 1048832,
        'SpellVisualID_1': 11818,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_Mask': 16712188,
        'Description_Lang_enUS': 'Your melee critical strikes have a chance to give you energy.',
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
    },
)


# =====================================================================================================================
# rogue-rework S1a A2: script bindings, proc rows and the retired talents' leftovers (WP-BRIEF section 8, U20, R8)
# =====================================================================================================================
# Wound Poison payload (spell_rog_wound_poison_mastery): eff0's aura 271 amount += Mastery / 2 with the Improved Poisons
# capstone 14115. Applied through the payload's own aura, so it reaches bleeds already running.
scripted_by(wound_poison_13218, 'spell_rog_wound_poison_mastery')

# Seal Fate: the stock -14186 row is re-declared on the single-strike builder group (d2 b19, C2). Multi-hit casts
# (Mutilate, Kingsbane, Fan of Knives) roll through Rogue::RollSealFate once per cast instead. ProcFlags 0 = the DBC's
# 87376 (melee auto + ability hits), chance 0 = the rank's own ProcChance 33/66/100, AttributesMask 2 (triggered casts
# may proc) and the 500 ms cooldown are the live row's values. Phase HIT, hit mask CRIT.
procs_on(-14186, proc_flags=0, family_name=8, family_mask=m.SEAL_FATE_PROC_READ, spell_phase_mask=2, hit_mask=2,
         attributes_mask=2, cooldown_ms=500)

# Focused Attacks keeps its stock -51634 proc row; the CheckProc fork rejects the Mutilate / Kingsbane hands and Fan of
# Knives (they resolve once per cast in C++).
unbind_script(-51634, 'spell_rog_focused_attacks')
scripted_by(-51634, 'spell_rog_focused_attacks_rework')

# Reworked talents whose stock C++ is replaced (the new behavior is in Rogue:: / spell_rogue_assassination.cpp), and the
# five stock proc rows that would keep firing: Ruthlessness, Quick Recovery and Deadly Brew are DUMMY / modifier ranks
# now (their DBC ProcTypeMask is 0 above), Cut to the Chase and Turn the Tables belong to the retired talents (A1).
unbind_script(-14143, 'spell_rog_remorseless_attacks')
unbind_script(-31244, 'spell_rog_quick_recovery')
unbind_script(-51625, 'spell_rog_deadly_brew')
unbind_script(-51664, 'spell_rog_cut_to_the_chase')
unbind_script(-51627, 'spell_rog_turn_the_tables')
unbind_script(52910, 'spell_rog_turn_the_tables_proc')
unbind_script(52914, 'spell_rog_turn_the_tables_proc')
unbind_script(52915, 'spell_rog_turn_the_tables_proc')
remove_spell_proc(-14156)
remove_spell_proc(-31244)
remove_spell_proc(-51625)
remove_spell_proc(-51664)
remove_spell_proc(-51627)


# ---- rogue-rework S2a WP-0.2: stock-only Subtlety rank spells pulled unedited (pull_dsl.py --constants) ----
# Heightened Senses 30894 / 30895, Deadliness 30902-30904, Enveloping Shadows 31211-31213, Honor Among Thieves 51698 /
# 51700 / 51701, and Cheat Death's buff Cheating Death 45182 (S2a 0-verify C2: stock is a DUMMY aura). Untouched reference
# copies (generate.py skips them) until A2 rewrites them in place per the S2a WP-BRIEF.
heightened_senses_30894 = spell(
    id=30894,
    name='Heightened Senses',
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
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=290),
    ],
    spell_icon_id=103,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Heightened Senses": eff0 aura 290 MOD_CRIT_PCT +1 (melee, ranged and '
        'spell crit; R10); the stock detection (aura 17) and hit-avoidance (185 / 186) effects are gone.'
    ),
    raw_overrides={
        'CastingTimeIndex': 1,
        'ProcChance': 101,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': _with_cap('Increases your critical strike chance by $s1%.', 'Capstone: Your Stealth detection is increased.', False),
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'SpellClassSet': 8,
    },
)


heightened_senses_30895 = spell(
    id=30895,
    name='Heightened Senses',
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
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=290),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=17),
    ],
    spell_icon_id=103,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Heightened Senses": eff0 aura 290 MOD_CRIT_PCT +2; eff1 aura 17 '
        'MOD_STEALTH_DETECT +6 (the capstone, the stock rank 2 amount); aura 185 / 186 are gone.'
    ),
    raw_overrides={
        'CastingTimeIndex': 1,
        'ProcChance': 101,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': _with_cap('Increases your critical strike chance by $s1%.', 'Capstone: Your Stealth detection is increased.', True),
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'SpellClassSet': 8,
    },
)


deadliness_30902 = spell(
    id=30902,
    name='Deadliness',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_ATTACK_POWER_PCT),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=22),
    ],
    spell_icon_id=1972,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Deadliness": eff0 aura 166 attack power +2% (stock), eff1 pct DOT +2 on '
        'Garrote and Rupture (DEADLINESS_DOT_READ).'
    ),
    raw_overrides={
        'CastingTimeIndex': 1,
        'ProcChance': 101,
        'DurationIndex': 0,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases your attack power by $s1%, and the damage of your Garrote and Rupture by $s2%.',
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'SpellClassSet': 8,
        **m.read_mask_keys(1, m.DEADLINESS_DOT_READ),
    },
)


deadliness_30903 = spell(
    id=30903,
    name='Deadliness',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.MOD_ATTACK_POWER_PCT),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=22),
    ],
    spell_icon_id=1972,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Deadliness": eff0 aura 166 attack power +4% (stock), eff1 pct DOT +4 on '
        'Garrote and Rupture (DEADLINESS_DOT_READ).'
    ),
    raw_overrides={
        'CastingTimeIndex': 1,
        'ProcChance': 101,
        'DurationIndex': 0,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases your attack power by $s1%, and the damage of your Garrote and Rupture by $s2%.',
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'SpellClassSet': 8,
        **m.read_mask_keys(1, m.DEADLINESS_DOT_READ),
    },
)


deadliness_30904 = spell(
    id=30904,
    name='Deadliness',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.MOD_ATTACK_POWER_PCT),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=22),
    ],
    spell_icon_id=1972,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Deadliness": eff0 aura 166 attack power +6% (stock), eff1 pct DOT +6 on '
        'Garrote and Rupture (DEADLINESS_DOT_READ).'
    ),
    raw_overrides={
        'CastingTimeIndex': 1,
        'ProcChance': 101,
        'DurationIndex': 0,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases your attack power by $s1%, and the damage of your Garrote and Rupture by $s2%.',
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'SpellClassSet': 8,
        **m.read_mask_keys(1, m.DEADLINESS_DOT_READ),
    },
)


enveloping_shadows_31211 = spell(
    id=31211,
    name='Enveloping Shadows',
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
    ],
    spell_icon_id=2111,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Enveloping Shadows": hidden DUMMY 2 (the % the helper 204173 reads: '
        'GetRankAmount EFFECT_0). The stock area-damage aura 229 is gone (Feint covers area damage).'
    ),
    raw_overrides={
        'CastingTimeIndex': 1,
        'ProcChance': 101,
        'DurationIndex': 0,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Reduces the physical damage you take by $s1% while Ghostly Veil is active.',
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'SpellClassSet': 8,
    },
)


enveloping_shadows_31212 = spell(
    id=31212,
    name='Enveloping Shadows',
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
    spell_icon_id=2111,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Enveloping Shadows": hidden DUMMY 4 (the % the helper 204173 reads: '
        'GetRankAmount EFFECT_0). The stock area-damage aura 229 is gone (Feint covers area damage).'
    ),
    raw_overrides={
        'CastingTimeIndex': 1,
        'ProcChance': 101,
        'DurationIndex': 0,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Reduces the physical damage you take by $s1% while Ghostly Veil is active.',
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'SpellClassSet': 8,
    },
)


enveloping_shadows_31213 = spell(
    id=31213,
    name='Enveloping Shadows',
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
    spell_icon_id=2111,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Enveloping Shadows": hidden DUMMY 6 (the % the helper 204173 reads: '
        'GetRankAmount EFFECT_0). The stock area-damage aura 229 is gone (Feint covers area damage).'
    ),
    raw_overrides={
        'CastingTimeIndex': 1,
        'ProcChance': 101,
        'DurationIndex': 0,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Reduces the physical damage you take by $s1% while Ghostly Veil is active.',
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'SpellClassSet': 8,
    },
)


honor_among_thieves_51698 = spell(
    id=51698,
    name='Honor Among Thieves',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=290),
    ],
    spell_icon_id=2903,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Honor Among Thieves": eff0 APPLY_AURA (type 6, not 35) aura 290 '
        'MOD_CRIT_PCT +1, radius 0; the stock party-crit combo point proc is gone (raw ProcTypeMask 0 / ProcChance '
        '101, the three spell_proc rows removed and the stock scripts unbound below); the junk eff1 zeroed. The '
        'capstone (51701 held) is read by Rogue::OnFinisherCrit (buff 204172).'
    ),
    raw_overrides={
        'AttributesEx3': 67109120,
        'AttributesEx4': 524288,
        'CastingTimeIndex': 1,
        'ProcTypeMask': 0,
        'ProcChance': 101,
        'DurationIndex': 0,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'EffectDieSides_2': 0,
        'EffectBasePoints_2': 0,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': _with_cap('Increases your critical strike chance by $s1%.', 'Capstone: When one of your finishing moves critically strikes, you and one nearby ally deal $204172s1% more damage for $204172d.', False),
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'SpellClassSet': 8,
        **m.clear_mask_keys(1),
    },
)


honor_among_thieves_51700 = spell(
    id=51700,
    name='Honor Among Thieves',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=290),
    ],
    spell_icon_id=2903,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Honor Among Thieves": eff0 APPLY_AURA (type 6, not 35) aura 290 '
        'MOD_CRIT_PCT +2, radius 0; the stock party-crit combo point proc is gone (raw ProcTypeMask 0 / ProcChance '
        '101, the three spell_proc rows removed and the stock scripts unbound below); the junk eff1 zeroed. The '
        'capstone (51701 held) is read by Rogue::OnFinisherCrit (buff 204172).'
    ),
    raw_overrides={
        'AttributesEx3': 67109120,
        'AttributesEx4': 524288,
        'CastingTimeIndex': 1,
        'ProcTypeMask': 0,
        'ProcChance': 101,
        'SpellLevel': 1,
        'DurationIndex': 0,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'EffectDieSides_2': 0,
        'EffectBasePoints_2': 0,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': _with_cap('Increases your critical strike chance by $s1%.', 'Capstone: When one of your finishing moves critically strikes, you and one nearby ally deal $204172s1% more damage for $204172d.', False),
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'SpellClassSet': 8,
        **m.clear_mask_keys(1),
    },
)


honor_among_thieves_51701 = spell(
    id=51701,
    name='Honor Among Thieves',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=290),
    ],
    spell_icon_id=2903,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Honor Among Thieves": eff0 APPLY_AURA (type 6, not 35) aura 290 '
        'MOD_CRIT_PCT +3, radius 0; the stock party-crit combo point proc is gone (raw ProcTypeMask 0 / ProcChance '
        '101, the three spell_proc rows removed and the stock scripts unbound below); the junk eff1 zeroed. The '
        'capstone (51701 held) is read by Rogue::OnFinisherCrit (buff 204172).'
    ),
    raw_overrides={
        'AttributesEx3': 67109120,
        'AttributesEx4': 524288,
        'CastingTimeIndex': 1,
        'ProcTypeMask': 0,
        'ProcChance': 101,
        'SpellLevel': 1,
        'DurationIndex': 0,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'EffectDieSides_2': 0,
        'EffectBasePoints_2': 0,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': _with_cap('Increases your critical strike chance by $s1%.', 'Capstone: When one of your finishing moves critically strikes, you and one nearby ally deal $204172s1% more damage for $204172d.', True),
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'SpellClassSet': 8,
        **m.clear_mask_keys(1),
    },
)


cheating_death_45182 = spell(
    id=45182,
    name='Cheating Death',
    school=School.NORMAL,
    attributes=150994960,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=3000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-91, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
    ],
    spell_icon_id=2109,
    notes=(
        'rogue-rework S2a A2, Subtlety doc "Cheat Death": pulled from the stock DUMMY aura and retyped (S2a 0-verify '
        'C2): eff0 aura 87 MOD_DAMAGE_PERCENT_TAKEN -90% (misc 127: every school), 3 s (unchanged), visible, aura '
        'text number-free; the stale 0x400000 masks cleared. Cast by spell_rog_cheat_death_rework with the shared '
        'marker 200193.'
    ),
    raw_overrides={
        'AttributesEx4': 128,
        'CastingTimeIndex': 1,
        'ProcChance': 101,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'SpellVisualID_1': 10423,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_Mask': 16712172,
        'Description_Lang_enUS': 'All damage you take is reduced by $s1% for $d.',
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_enUS': 'Damage taken reduced.',
        'AuraDescription_Lang_Mask': 16712190,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'SpellClassSet': 8,
        **m.clear_mask_keys(0, 1),
    },
)


# ---- rogue-rework S2a A2: Subtlety script bindings and proc rows (WP-BRIEF section 8, R1, R9, R22) ----
# Honor Among Thieves: the stock party-crit combo point proc is retired (the ranks are a crit aura now, the capstone buff
# 204172 is applied by Rogue::OnFinisherCrit). The three rank scripts, the proc payload script and the three spell_proc
# rows go; the ranks carry raw ProcTypeMask 0 so no default row is built either. No spell_group 1288 (R9).
unbind_script(51698, 'spell_rog_honor_among_thieves')
unbind_script(51700, 'spell_rog_honor_among_thieves')
unbind_script(51701, 'spell_rog_honor_among_thieves')
unbind_script(52916, 'spell_rog_honor_among_thieves_proc')
remove_spell_proc(51698)
remove_spell_proc(51700)
remove_spell_proc(51701)

# Setup (the retired talent 246): script and proc row go; the retired ranks keep their DBC flags, inert (unlearned).
unbind_script(-13983, 'spell_rog_setup')
remove_spell_proc(-13983)

# Waylay and Throwing Specialization: the stock proc rows go (r1 is a plain modifier now, the interrupt chain is cut).
remove_spell_proc(-51692)
remove_spell_proc(-5952)
remove_spell_proc(32748)

# Initiative (R1): aura 42 -> 13977 on Ambush / Garrote / Cheap Shot, melee ability hits (PROC_FLAG_DONE_SPELL_MELEE_DMG_
# CLASS 0x10: all three buttons are DefenseType 2), phase HIT, hit mask 0 = NORMAL | CRIT for a DONE proc (a dodge never
# procs). Chance 0 = the rank's own raw ProcChance 33 / 66 / 100 through Aura::CalcProcChance x Proc Chance. Cheap Shot
# (no damage) fires it; a triggered Garrote (Cut Throat) cannot.
procs_on(-13976, proc_flags=0x10, family_name=8, family_mask=m.INITIATIVE_PROC_READ, spell_phase_mask=2)

# Waylay rank 2 (R1): the capstone slow 51693, 100% on an Ambush hit. The rank's raw ProcTypeMask 16 stays.
procs_on(51696, proc_flags=0x10, family_name=8, family_mask=m.WAYLAY_READ, spell_phase_mask=2, chance=100)

# Cheat Death (R22): the stock spell_rog_cheat_death (spell_rogue.cpp, "reduce you to 10% health") is replaced by the
# Ardent-Defender-shaped fork in spell_rogue_subtlety.cpp.
unbind_script(-31228, 'spell_rog_cheat_death')
scripted_by(-31228, 'spell_rog_cheat_death_rework')


# ---- rogue-rework S3a WP-0.2: stock-only Combat rank spells pulled unedited (pull_dsl.py --constants) ----
# Precision 13705 / 13832 / 13843, Lightning Reflexes 13712 / 13788 / 13789, Mace (to be Weapon) Specialization 13709 /
# 13800 / 13801, Hack and Slash 13960-13962, Unfair Advantage 51672 / 51674 and its strikes 51675 / 51677 (S3a 0-verify
# C1), Prey on the Weak 51685-51687, Killing Spree strikes 57841 / 57842 (moved here from source/spells/npc.csv).
# Untouched reference copies (generate.py skips them) until A2 rewrites them in place per the S3a WP-BRIEF.
precision_13705 = spell(
    id=13705,
    name='Precision',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=290),
    ],
    spell_icon_id=126,
    notes=(
        'rogue-rework S3a A2, Combat doc "Precision": eff0 aura 290 MOD_CRIT_PCT +1; the stock hit auras (54 / 55) are gone; weapon requirement dropped (R7).'
    ),
    raw_overrides={
        'CastingTimeIndex': 1,
        'ProcChance': 101,
        'DurationIndex': 0,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases your critical strike chance by $s1%.',
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EffectBonusMultiplier_1': 1.0,
        'ProcTypeMask': 0,
        **m.clear_mask_keys(0, 1, 2),
    },
)


precision_13832 = spell(
    id=13832,
    name='Precision',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=290),
    ],
    spell_icon_id=126,
    notes=(
        'rogue-rework S3a A2, Combat doc "Precision": eff0 aura 290 MOD_CRIT_PCT +2; the stock hit auras (54 / 55) are gone; weapon requirement dropped (R7).'
    ),
    raw_overrides={
        'CastingTimeIndex': 1,
        'ProcChance': 101,
        'DurationIndex': 0,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases your critical strike chance by $s1%.',
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EffectBonusMultiplier_1': 1.0,
        'ProcTypeMask': 0,
        **m.clear_mask_keys(0, 1, 2),
    },
)


precision_13843 = spell(
    id=13843,
    name='Precision',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=290),
    ],
    spell_icon_id=126,
    notes=(
        'rogue-rework S3a A2, Combat doc "Precision": eff0 aura 290 MOD_CRIT_PCT +3; the stock hit auras (54 / 55) are gone; weapon requirement dropped (R7).'
    ),
    raw_overrides={
        'CastingTimeIndex': 1,
        'ProcChance': 101,
        'DurationIndex': 0,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases your critical strike chance by $s1%.',
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EffectBonusMultiplier_1': 1.0,
        'ProcTypeMask': 0,
        **m.clear_mask_keys(0, 1, 2),
    },
)


lightning_reflexes_13712 = spell(
    id=13712,
    name='Lightning Reflexes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_DODGE_PERCENT),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=138),
    ],
    spell_icon_id=30,
    notes=(
        'rogue-rework S3a A2, Combat doc "Lightning Reflexes": eff0 dodge +2% (stock), eff1 aura 138 melee haste +3% (stock 4 / 7 / 10).'
    ),
    raw_overrides={
        'CastingTimeIndex': 1,
        'ProcChance': 101,
        'DurationIndex': 0,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases your Dodge chance by $s1% and gives you $s2% melee haste.',
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EffectBonusMultiplier_1': 1.0,
        'ProcTypeMask': 0,
        **m.clear_mask_keys(0, 1, 2),
    },
)


lightning_reflexes_13788 = spell(
    id=13788,
    name='Lightning Reflexes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.MOD_DODGE_PERCENT),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=138),
    ],
    spell_icon_id=30,
    notes=(
        'rogue-rework S3a A2, Combat doc "Lightning Reflexes": eff0 dodge +4% (stock), eff1 aura 138 melee haste +6% (stock 4 / 7 / 10).'
    ),
    raw_overrides={
        'CastingTimeIndex': 1,
        'ProcChance': 101,
        'DurationIndex': 0,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases your Dodge chance by $s1% and gives you $s2% melee haste.',
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EffectBonusMultiplier_1': 1.0,
        'ProcTypeMask': 0,
        **m.clear_mask_keys(0, 1, 2),
    },
)


lightning_reflexes_13789 = spell(
    id=13789,
    name='Lightning Reflexes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.MOD_DODGE_PERCENT),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=138),
    ],
    spell_icon_id=30,
    notes=(
        'rogue-rework S3a A2, Combat doc "Lightning Reflexes": eff0 dodge +6% (stock), eff1 aura 138 melee haste +10% (stock 4 / 7 / 10).'
    ),
    raw_overrides={
        'CastingTimeIndex': 1,
        'ProcChance': 101,
        'DurationIndex': 0,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases your Dodge chance by $s1% and gives you $s2% melee haste.',
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EffectBonusMultiplier_1': 1.0,
        'ProcTypeMask': 0,
        **m.clear_mask_keys(0, 1, 2),
    },
)


weapon_specialization_13709 = spell(
    id=13709,
    name='Weapon Specialization',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=280, misc_value=1),
    ],
    spell_icon_id=367,
    notes=(
        'rogue-rework S3a A2, Combat doc "Weapon Specialization" (renamed from Mace Specialization, R7): eff0 aura 280 armor penetration +5% (stock 3 / 6 / 9), any weapon (EquippedItemClass -1).'
    ),
    raw_overrides={
        'CastingTimeIndex': 1,
        'ProcChance': 101,
        'SpellLevel': 1,
        'DurationIndex': 0,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'SpellPriority': 50,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases your armor penetration by $s1%.',
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'ProcTypeMask': 0,
        **m.clear_mask_keys(0, 1, 2),
    },
)


weapon_specialization_13800 = spell(
    id=13800,
    name='Weapon Specialization',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=280, misc_value=1),
    ],
    spell_icon_id=367,
    notes=(
        'rogue-rework S3a A2, Combat doc "Weapon Specialization" (renamed from Mace Specialization, R7): eff0 aura 280 armor penetration +10% (stock 3 / 6 / 9), any weapon (EquippedItemClass -1).'
    ),
    raw_overrides={
        'CastingTimeIndex': 1,
        'ProcChance': 101,
        'SpellLevel': 1,
        'DurationIndex': 0,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'EffectDieSides_2': 1,
        'EffectBasePoints_2': -1,
        'SpellPriority': 50,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases your armor penetration by $s1%.',
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'ProcTypeMask': 0,
        **m.clear_mask_keys(0, 1, 2),
    },
)


weapon_specialization_13801 = spell(
    id=13801,
    name='Weapon Specialization',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=280, misc_value=1),
    ],
    spell_icon_id=367,
    notes=(
        'rogue-rework S3a A2, Combat doc "Weapon Specialization" (renamed from Mace Specialization, R7): eff0 aura 280 armor penetration +15% (stock 3 / 6 / 9), any weapon (EquippedItemClass -1).'
    ),
    raw_overrides={
        'CastingTimeIndex': 1,
        'ProcChance': 101,
        'SpellLevel': 1,
        'DurationIndex': 0,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'EffectDieSides_2': 1,
        'EffectBasePoints_2': -1,
        'SpellPriority': 50,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases your armor penetration by $s1%.',
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'ProcTypeMask': 0,
        **m.clear_mask_keys(0, 1, 2),
    },
)


hack_and_slash_13960 = spell(
    id=13960,
    name='Hack and Slash',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1462,
    notes=(
        'rogue-rework S3a A2, Combat doc "Hack and Slash": eff0 DUMMY 33 (weapon %, the strikes\' bp; read by GetRankAmount), any one-hander (the script checks the hitting hand). The proc row -13960 (flags 0x14, chance 100) and spell_rog_hack_and_slash roll it; raw ProcTypeMask 20 kept, the row\'s chance overrides ProcChance.'
    ),
    raw_overrides={
        'AttributesEx3': 524288,
        'CastingTimeIndex': 1,
        'ProcTypeMask': 20,
        'ProcChance': 1,
        'SpellLevel': 1,
        'DurationIndex': 0,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'SpellPriority': 50,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': f"Gives you a {_c(HACK_AND_SLASH_CHANCE_PCT)}% chance to get an extra attack with both weapons, dealing $s1% weapon damage, after hitting your target with a one-handed weapon.",
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        **m.clear_mask_keys(0, 1, 2),
    },
)


hack_and_slash_13961 = spell(
    id=13961,
    name='Hack and Slash',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=65, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1462,
    notes=(
        'rogue-rework S3a A2, Combat doc "Hack and Slash": eff0 DUMMY 66 (weapon %, the strikes\' bp; read by GetRankAmount), any one-hander (the script checks the hitting hand). The proc row -13960 (flags 0x14, chance 100) and spell_rog_hack_and_slash roll it; raw ProcTypeMask 20 kept, the row\'s chance overrides ProcChance.'
    ),
    raw_overrides={
        'AttributesEx3': 524288,
        'CastingTimeIndex': 1,
        'ProcTypeMask': 20,
        'ProcChance': 2,
        'SpellLevel': 1,
        'DurationIndex': 0,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'SpellPriority': 50,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': f"Gives you a {_c(HACK_AND_SLASH_CHANCE_PCT)}% chance to get an extra attack with both weapons, dealing $s1% weapon damage, after hitting your target with a one-handed weapon.",
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        **m.clear_mask_keys(0, 1, 2),
    },
)


hack_and_slash_13962 = spell(
    id=13962,
    name='Hack and Slash',
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
    ],
    spell_icon_id=1462,
    notes=(
        'rogue-rework S3a A2, Combat doc "Hack and Slash": eff0 DUMMY 100 (weapon %, the strikes\' bp; read by GetRankAmount), any one-hander (the script checks the hitting hand). The proc row -13960 (flags 0x14, chance 100) and spell_rog_hack_and_slash roll it; raw ProcTypeMask 20 kept, the row\'s chance overrides ProcChance.'
    ),
    raw_overrides={
        'AttributesEx3': 524288,
        'CastingTimeIndex': 1,
        'ProcTypeMask': 20,
        'ProcChance': 3,
        'SpellLevel': 1,
        'DurationIndex': 0,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'SpellPriority': 50,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': f"Gives you a {_c(HACK_AND_SLASH_CHANCE_PCT)}% chance to get an extra attack with both weapons, dealing $s1% weapon damage, after hitting your target with a one-handed weapon.",
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        **m.clear_mask_keys(0, 1, 2),
    },
)


unfair_advantage_51672 = spell(
    id=51672,
    name='Unfair Advantage',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=51675),
    ],
    spell_icon_id=2964,
    notes=(
        'rogue-rework S3a A2, Combat doc "Unfair Advantage": eff0 aura 42 -> strike 51675 (stock); stale A_1 0x20006 cleared (R1). The proc row -51672 (flags 0x2028 dodge | parry, hit mask 0x30, 2 s) is declared at the end of this file.'
    ),
    raw_overrides={
        'CastingTimeIndex': 1,
        'ProcTypeMask': 8232,
        'ProcChance': 100,
        'DurationIndex': 0,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'SpellVisualID_1': 11822,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': f"Whenever you dodge or parry an attack you gain an Unfair Advantage, striking back for $51675s2% of your main hand weapon's damage. This cannot occur more than once per {_sec(UNFAIR_ADVANTAGE_ICD_MS)} sec.",
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_2': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        **m.clear_mask_keys(0, 1, 2),
    },
)


unfair_advantage_51674 = spell(
    id=51674,
    name='Unfair Advantage',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=51677),
    ],
    spell_icon_id=2964,
    notes=(
        'rogue-rework S3a A2, Combat doc "Unfair Advantage": eff0 aura 42 -> strike 51677 (stock); stale A_1 0x20006 cleared (R1). The proc row -51672 (flags 0x2028 dodge | parry, hit mask 0x30, 2 s) is declared at the end of this file.'
    ),
    raw_overrides={
        'CastingTimeIndex': 1,
        'ProcTypeMask': 8232,
        'ProcChance': 100,
        'DurationIndex': 0,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'SpellVisualID_1': 11822,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': f"Whenever you dodge or parry an attack you gain an Unfair Advantage, striking back for $51677s2% of your main hand weapon's damage. This cannot occur more than once per {_sec(UNFAIR_ADVANTAGE_ICD_MS)} sec.",
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EffectBonusMultiplier_1': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        **m.clear_mask_keys(0, 1, 2),
    },
)


unfair_advantage_strike_51675 = spell(
    id=51675,
    name='Unfair Advantage',
    school=School.NORMAL,
    attributes=16,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.NORMALIZED_WEAPON_DMG, base_points=-1, implicit_target_a=6),
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, base_points=49, implicit_target_a=6),
    ],
    spell_icon_id=2964,
    notes=(
        'rogue-rework S3a A2, Combat doc "Unfair Advantage" strike: stock effects (50% main hand on eff1); SpellClassSet 8 with no family bits (C14) so the rogue hooks see it (Blade Flurry copies it); stale A_1 0x20006 cleared (R1).'
    ),
    raw_overrides={
        'AttributesEx4': 16384,
        'CastingTimeIndex': 1,
        'ProcChance': 101,
        'DurationIndex': 0,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'ImplicitTargetA_3': 1,
        'SpellVisualID_1': 39,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': "Whenever you dodge or parry an attack you gain an Unfair Advantage, striking back for $51675s2% of your main hand weapon's damage.",
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712190,
        'DefenseType': 2,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'SpellClassSet': 8,
        **m.class_mask_keys((0, 0, 0)),
        **m.clear_mask_keys(0, 1, 2),
    },
)


unfair_advantage_strike_51677 = spell(
    id=51677,
    name='Unfair Advantage',
    school=School.NORMAL,
    attributes=16,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.NORMALIZED_WEAPON_DMG, base_points=-1, implicit_target_a=6),
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, base_points=99, implicit_target_a=6),
    ],
    spell_icon_id=2964,
    notes=(
        'rogue-rework S3a A2, Combat doc "Unfair Advantage" strike: stock effects (100% main hand on eff1); SpellClassSet 8 with no family bits (C14) so the rogue hooks see it (Blade Flurry copies it); stale A_1 0x20006 cleared (R1).'
    ),
    raw_overrides={
        'AttributesEx4': 16384,
        'CastingTimeIndex': 1,
        'ProcChance': 101,
        'DurationIndex': 0,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'SpellVisualID_1': 39,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': "Whenever you dodge or parry an attack you gain an Unfair Advantage, striking back for $51677s2% of your main hand weapon's damage.",
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712190,
        'DefenseType': 2,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'SpellClassSet': 8,
        **m.class_mask_keys((0, 0, 0)),
        **m.clear_mask_keys(0, 1, 2),
    },
)


prey_on_the_weak_51685 = spell(
    id=51685,
    name='Prey on the Weak',
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
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2983,
    notes=(
        'rogue-rework S3a A2, Combat doc "Prey on the Weak": eff0 DUMMY 3 (damage %, read by GetRankAmount EFFECT_0), eff1 DUMMY 5 (crit %, EFFECT_1); stock periodic dummy, amplitude and stale masks gone (R8); the stock script spell_rog_prey_on_the_weak is unbound below.'
    ),
    raw_overrides={
        'CastingTimeIndex': 1,
        'ProcChance': 101,
        'DurationIndex': 0,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 1',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': f"Your damage is increased by $s1% against targets below {_c(PREY_DAMAGE_HEALTH_PCT)}% health. Your critical strike chance is increased by $s2% against targets above {_c(PREY_CRIT_HEALTH_PCT)}% health.",
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'ProcTypeMask': 0,
        **m.clear_mask_keys(0, 1, 2),
    },
)


prey_on_the_weak_51686 = spell(
    id=51686,
    name='Prey on the Weak',
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
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2983,
    notes=(
        'rogue-rework S3a A2, Combat doc "Prey on the Weak": eff0 DUMMY 6 (damage %, read by GetRankAmount EFFECT_0), eff1 DUMMY 10 (crit %, EFFECT_1); stock periodic dummy, amplitude and stale masks gone (R8); the stock script spell_rog_prey_on_the_weak is unbound below.'
    ),
    raw_overrides={
        'CastingTimeIndex': 1,
        'ProcChance': 101,
        'DurationIndex': 0,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 2',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': f"Your damage is increased by $s1% against targets below {_c(PREY_DAMAGE_HEALTH_PCT)}% health. Your critical strike chance is increased by $s2% against targets above {_c(PREY_CRIT_HEALTH_PCT)}% health.",
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'ProcTypeMask': 0,
        **m.clear_mask_keys(0, 1, 2),
    },
)


prey_on_the_weak_51687 = spell(
    id=51687,
    name='Prey on the Weak',
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
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2983,
    notes=(
        'rogue-rework S3a A2, Combat doc "Prey on the Weak": eff0 DUMMY 10 (damage %, read by GetRankAmount EFFECT_0), eff1 DUMMY 15 (crit %, EFFECT_1); stock periodic dummy, amplitude and stale masks gone (R8); the stock script spell_rog_prey_on_the_weak is unbound below.'
    ),
    raw_overrides={
        'CastingTimeIndex': 1,
        'ProcChance': 101,
        'DurationIndex': 0,
        'RangeIndex': 1,
        'EquippedItemClass': -1,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': 'Rank 3',
        'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': f"Your damage is increased by $s1% against targets below {_c(PREY_DAMAGE_HEALTH_PCT)}% health. Your critical strike chance is increased by $s2% against targets above {_c(PREY_CRIT_HEALTH_PCT)}% health.",
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EffectBonusMultiplier_3': 1.0,
        'ProcTypeMask': 0,
        **m.clear_mask_keys(0, 1, 2),
    },
)


killing_spree_main_57841 = spell(
    id=57841,
    name='Killing Spree',
    school=School.NORMAL,
    attributes=2424848,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.NORMALIZED_WEAPON_DMG, base_points=-1, implicit_target_a=6),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=6, trigger_spell=57842),
    ],
    spell_icon_id=2008,
    notes=(
        'rogue-rework S3a A2, Combat doc "Killing Spree" main-hand strike (moved from npc.csv): KILLING_SPREE_STRIKE_CLASS (d1 b23, so Coup de Grace reads it), Ex3 |= SUPPRESS_CASTER_PROCS 0x10000, Ex4 |= SUPPRESS_WEAPON_PROCS 0x800000 (R6 / U62); damage unchanged (normalized 100% per hand).'
    ),
    raw_overrides={
        'AttributesEx': 512,
        'AttributesEx2': 1073741824,
        'AttributesEx3': 67073,
        'CastingTimeIndex': 1,
        'ProcChance': 101,
        'BaseLevel': 1,
        'SpellLevel': 1,
        'RangeIndex': 2,
        'EquippedItemClass': 2,
        'EquippedItemSubclass': 173555,
        'SpellVisualID_1': 39,
        'SpellPriority': 50,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_Mask': 16712188,
        'Description_Lang_enUS': 'Step through the shadows from enemy to enemy within 10 yards, attacking an enemy every .5 secs with both weapons until 5 assaults are made.  Can hit the same target multiple times.',
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'SpellClassSet': 8,
        'DefenseType': 2,
        'PreventionType': 2,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'AttributesEx4': 8388608,
        **m.class_mask_keys(m.KILLING_SPREE_STRIKE_CLASS),
    },
)


killing_spree_off_57842 = spell(
    id=57842,
    name='Killing Spree',
    school=School.NORMAL,
    attributes=2424848,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.ENERGY,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.NORMALIZED_WEAPON_DMG, base_points=-1, implicit_target_a=6),
    ],
    spell_icon_id=83,
    notes=(
        'rogue-rework S3a A2, Combat doc "Killing Spree" off-hand strike (moved from npc.csv): KILLING_SPREE_STRIKE_CLASS (d1 b23), Ex3 |= SUPPRESS_CASTER_PROCS 0x10000, Ex4 |= SUPPRESS_WEAPON_PROCS 0x800000 (R6 / U62); damage unchanged.'
    ),
    raw_overrides={
        'AttributesEx': 16,
        'AttributesEx2': 1073741824,
        'AttributesEx3': 16843265,
        'AttributesEx4': 8388736,
        'CastingTimeIndex': 1,
        'BaseLevel': 1,
        'SpellLevel': 1,
        'RangeIndex': 1,
        'EquippedItemClass': 2,
        'EquippedItemSubclass': 173555,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_Mask': 16712188,
        'Description_Lang_enUS': 'Step through the shadows from enemy to enemy within 10 yards, attacking an enemy every .5 secs with both weapons until 5 assaults are made.  Can hit the same target multiple times.',
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_Mask': 16712188,
        'SpellClassSet': 8,
        'MaxTargets': 1,
        'DefenseType': 2,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EffectBonusMultiplier_1': 1.0,
        **m.class_mask_keys(m.KILLING_SPREE_STRIKE_CLASS),
    },
)


# =====================================================================================================================
# rogue-rework S3a A2: script bindings, proc rows and the retired talents' leftovers (WP-BRIEF section 8, R1, U63, U67)
# =====================================================================================================================
# Prey on the Weak: the stock script (a self aura 58670 while the rogue's health % > the victim's) is replaced by the
# Rogue:: health clause / crit debuff (-51685 expands over the whole chain 51685-51689).
unbind_script(-51685, 'spell_rog_prey_on_the_weak')

# Retired Combat talents (U67): Combat Potency and Nerves of Steel lose their scripts; Combat Potency's proc row and
# Blade Twisting's daze proc row (the ranks are DUMMY now, raw ProcTypeMask 0) are removed.
unbind_script(-35541, 'spell_rog_combat_potency')
unbind_script(-31130, 'spell_rog_nerves_of_steel')
remove_spell_proc(-35541)
remove_spell_proc(-31124)

# Hack and Slash (U63): the stock -13960 row is replaced. Phase HIT, spell type DAMAGE (1), proc flags 0x14 (melee auto
# + melee ability hit), chance 100: spell_rog_hack_and_slash's CheckProc (Rogue::RollHackAndSlash) rolls the real
# 6% x Proc Chance (x weapon speed / 2600 on autos) and OnProc casts the strikes.
procs_on(-13960, 0x14, spell_type_mask=1, spell_phase_mask=2, chance=100)
scripted_by(-13960, 'spell_rog_hack_and_slash')

# Unfair Advantage (R1 / C12): dodge | parry (hit mask 0x30; the stock row had dodge only, 1 s), 2 s internal cooldown.
# proc_flags is the second positional argument (registry.procs_on), chance 0 = the rank's own DBC 100.
procs_on(-51672, 0x2028, hit_mask=0x30, cooldown_ms=int(UNFAIR_ADVANTAGE_ICD_MS['value']))
