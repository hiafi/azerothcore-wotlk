"""
Deathknight - spells that are never directly cast - proc/periodic-tick effects, trigger_spell targets, hidden talent-rank buffs, etc..

Split from a single source/classes/deathknight.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .deathknight_...` below) resolve.
"""

from lib.dsl import AuraType, DispelType, Effect, EffectType, Mechanic, PowerType, RANGE_SELF, School, SpellModOp
from lib.dsl.registry import (
    bonus_coefficients, const, custom_attr, linked_spell, pot_text, procs_on, product, remove_spell_proc, scripted_by, spell,
    talent_mult, tooltip_vars, unbind_bonus_coefficients, unbind_script,
)

from . import _masks as m
from .deathknight_blood import bloody_strikes_tooltip_1250, improved_death_strike_tooltip_1251
from .deathknight_frost_b import avalanche_203321

# =====================================================================================================================
# S2a (Frost): the talent-rank helper, the tooltip_vars entries 1254 / 1255 and Avalanche's potency text
# =====================================================================================================================
_SPELLFAMILY_DEATHKNIGHT = 15
_ATTR0_TALENT_PASSIVE = 464                  # ABILITY 0x10 | PASSIVE 0x40 | DO_NOT_DISPLAY 0x80 | DO_NOT_LOG 0x100
_ATTR3_CAN_PROC_FROM_PROCS = 0x4000000       # SPELL_ATTR3_CAN_PROC_FROM_PROCS (a triggered cast may proc the aura)
_TARGET_SELF = 1
_CR_VERSATILITY = 1 << 21                    # MOD_CUSTOM_STAT_PCT misc: bit of CombatRating VERSATILITY (21)


def _frost_level(row, rank):
    """Talent-rank SpellLevel = 9 + 5 x grid row + rank (S1a D3, S2 brief L6)."""
    return 9 + 5 * row + rank


def _frost_rank(spell_id, name, rank, row, icon, effects, description, notes, school=School.NORMAL,
                attributes=_ATTR0_TALENT_PASSIVE, proc_chance=101, proc_type_mask=None, attributes_ex3=None,
                class_mask_1=None, equipped=None, masks=None, extra_raw=None, aura_description=None):
    """A rebuilt Frost talent rank spell: a hidden passive on the caster, family 15, self range, SpellLevel by grid row
    and rank. The raw_overrides are built from scratch, so no stale twin of the stock row survives; `masks` maps a
    1-based effect index to its (d0, d1, d2) EffectSpellClassMask triple, `equipped` is (EquippedItemClass,
    EquippedItemSubclass) for a rank that keeps the stock weapon requirement."""
    raw = {
        'CastingTimeIndex': 1, 'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'SpellLevel': _frost_level(row, rank),
        'ProcChance': proc_chance, 'EquippedItemClass': -1,
        'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': f'Rank {rank}',
        'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': description, 'AuraDescription_Lang_Mask': 16712188,
    }
    if aura_description:
        raw['AuraDescription_Lang_Mask'] = 16712190
        raw['AuraDescription_Lang_enUS'] = aura_description
    if equipped:
        raw['EquippedItemClass'], raw['EquippedItemSubclass'] = equipped
    if proc_type_mask is not None:
        raw['ProcTypeMask'] = proc_type_mask
    if attributes_ex3:
        raw['AttributesEx3'] = attributes_ex3
    if class_mask_1:
        raw['SpellClassMask_1'] = class_mask_1
    for i in range(1, 4):
        raw[f'EffectChainAmplitude_{i}'] = 1.0
    for effect_index, triple in (masks or {}).items():
        for dword, value in enumerate(triple, start=1):
            if value:
                raw[f'EffectSpellClassMask{"ABC"[effect_index - 1]}_{dword}'] = value
    raw.update(extra_raw or {})
    return spell(
        id=spell_id, name=name, school=school, attributes=attributes, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        effects=effects, spell_icon_id=icon, notes=''.join(notes), raw_overrides=raw,
    )


# Rime's capstone line quotes Avalanche's potency through its own declaration (deathknight_frost_b.py; that file must not
# import this one, or the import cycle breaks the load order).
_AVALANCHE_POT = pot_text(avalanche_203321)

# U24 (S2-HANDOFF, user 2026-10-24): spell-named unconditional % talents show on the tooltip.
# 1254 Heart Strike + Plague Strike: Gravefrost (203275-203277 eff0 SPELLMOD_DAMAGE +5/10/15%). Heart Strike keeps the
#   Bloody Strikes multiplier it read from entry 1250, so `heart` is the product of the two; its text is unchanged.
heart_plague_strike_tooltip_1254 = tooltip_vars(
    1254, 'Heart Strike (Bloody Strikes x Gravefrost) and Plague Strike (Gravefrost) damage on their tooltips',
    bs_heart=talent_mult([48977, 49394, 49395], effect=1),
    gravefrost=talent_mult([203275, 203276, 203277], effect=1),
    heart=product('bs_heart', 'gravefrost'),
)
# 1255 Icy Touch: Improved Icy Touch (49175 / 50031 / 51456 eff0 DUMMY +5/10/15%).
icy_touch_tooltip_1255 = tooltip_vars(
    1255, 'Icy Touch: Improved Icy Touch damage on the Icy Touch tooltip',
    iit=talent_mult([49175, 50031, 51456], effect=1),
)


plague_strike_45462 = spell(
    id=45462,
    name='Plague Strike',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=121, base_points=124, points_per_level=10.12, implicit_target_a=6),
        Effect(type=31, weapon_potency=49, implicit_target_a=6),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=6, trigger_spell=55078),
    ],
    spell_icon_id=2719,
    tooltip_vars=heart_plague_strike_tooltip_1254,
    notes=(
        'S2a (U24): tooltip reads Gravefrost (tooltip_vars 1254, $gravefrost) on the weapon percent and the flat; the stock '
        'SpellDescriptionVariableID 81 ($weapon, $bonus = $m1 * $m2 / 100) is replaced by the same maths in the text. '
        'pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept '
        'from rank 1 (learn level 55); RealPointsPerLevel from rank1->covers-60-overridden '
        '(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/'
        'mana_cost_pct from max rank. potency-system (PLAN P7 Death Knight pass, 2026-10-01): '
        'eff2 (WEAPON_PERCENT_DAMAGE) converted to weapon_potency=49 (same off-by-one fix as '
        'Mangle/Swipe/Shred - base_points=49 was dealing 50% live). The flat eff1 '
        '(NORMALIZED_WEAPON_DMG) is left hand-set, same reasoning as the Feral pass\'s Mangle/'
        'Swipe/Shred: far larger than weapon_potency\'s WEAPON_FLAT_BONUS_MAX=10 budget.'
    ),
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712190, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A vicious strike that deals ${$m2*$<gravefrost>}% weapon damage plus ${$m1*$m2/100*$<gravefrost>} and infects the target with Blood Plague, a disease dealing Shadow damage over time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'RuneCostID': 221, 'SpellClassMask_1': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50, 'SpellVisualID_1': 11624, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


icy_touch_45477 = spell(
    id=45477,
    name='Icy Touch',
    school=School.FROST,
    dispel=DispelType.MAGIC,
    attributes=262144,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=20.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=136.1, potency_kind='direct', implicit_target_a=6),
        Effect(type=EffectType.TRIGGER_SPELL, points_per_level=4.36, die_sides=0, implicit_target_a=6, trigger_spell=55095),
    ],
    spell_icon_id=2721,
    tooltip_vars=icy_touch_tooltip_1255,
    notes=(
        'S2a (U24): tooltip reads Improved Icy Touch (tooltip_vars 1255, $iit) on the damage via {pot1*iit}; the stale '
        '"Very high threat when in Frost Presence" sentence is dropped (Frost Presence is retired). '
        'pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept '
        'from rank 1 (learn level 55); RealPointsPerLevel from rank1->covers-60-overridden '
        '(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/'
        'mana_cost_pct from max rank. potency-system (PLAN P7 Death Knight pass, 2026-10-01): '
        'eff1 (SCHOOL_DAMAGE) converted to ap_potency=136.1 (deathknight-potency-report.md / '
        'deathknight-potency-proposals.txt - mismatch row, old AP-coefficient-implied potency '
        'was 23.3, the base-damage-implied 136.1 wins per the user-reviewed proposal). DieSides '
        '11 replaced by the system-standard +-5% roll.'
    ),
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx5': 32, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Melee and ranged attack speed reduced by $55095s2%.', 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Chills the target for {pot1*iit} Frost damage and infects them with Frost Fever, a disease that deals periodic damage and reduces melee and ranged attack speed by $55095s2% for $55095d.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 14684919, 'EffectSpellClassMaskB_1': 12589815, 'EffectSpellClassMaskC_1': 4194437, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'ImplicitTargetA_3': 6, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RuneCostID': 241, 'SpellClassMask_1': 2, 'SpellClassSet': 15, 'SpellLevel': 2, 'SpellPriority': 50, 'SpellVisualID_1': 11152, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


chains_of_ice_45524 = spell(
    id=45524,
    name='Chains of Ice',
    school=School.FROST,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=20.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-96, mechanic=Mechanic.SNARE, implicit_target_a=6, apply_aura=AuraType.MOD_DECREASE_SPEED),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=6, apply_aura=226, amplitude=1000),
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=180,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 134217728, 'AttributesEx4': 2048, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Slowed by frozen chains.', 'BaseLevel': 22, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shackles the target with frozen chains, reducing their movement by $s1%, and infects them with Frost Fever.  The target regains $s2% of their movement each second for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RuneCostID': 261, 'SpellClassMask_1': 4, 'SpellClassMask_2': 49152, 'SpellClassSet': 15, 'SpellLevel': 22, 'SpellVisualID_1': 12328, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetCreatureType': 1023},
)


blood_strike_45902 = spell(
    id=45902,
    name='Blood Strike',
    school=School.NORMAL,
    attributes=262160,
    category=1207,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=121, base_points=259, points_per_level=20.16, implicit_target_a=6),
        Effect(type=31, weapon_potency=39, implicit_target_a=6),
    ],
    spell_icon_id=2624,
    notes=(
        'pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept '
        'from rank 1 (learn level 55); RealPointsPerLevel from rank1->covers-60-overridden '
        '(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/'
        'mana_cost_pct from max rank. potency-system (PLAN P7 Death Knight pass, 2026-10-01): '
        'eff2 (WEAPON_PERCENT_DAMAGE) converted to weapon_potency=39 (same off-by-one fix as '
        'Mangle/Swipe/Shred - base_points=39 was dealing 40% live). The flat eff1 '
        '(NORMALIZED_WEAPON_DMG) is left hand-set, same reasoning as the Feral pass\'s Mangle/'
        'Swipe/Shred: far larger than weapon_potency\'s WEAPON_FLAT_BONUS_MAX=10 budget.'
    ),
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly strike the enemy, causing $s2% weapon damage plus $<bonus>, total damage increased by ${$m3/2}.1% for each of your diseases on the target.', 'EffectBasePoints_3': 24, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'RuneCostID': 301, 'SpellClassMask_1': 4194304, 'SpellClassSet': 15, 'SpellDescriptionVariableID': 102, 'SpellLevel': 1, 'SpellVisualID_1': 11148, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


blood_boil_48721 = spell(
    id=48721,
    name='Blood Boil',
    school=School.SHADOW,
    attributes=262144,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=92.0, potency_kind='direct', implicit_target_a=18, implicit_target_b=16, radius_yards=10.0),
    ],
    spell_icon_id=2725,
    tooltip_vars=bloody_strikes_tooltip_1250,
    notes=(
        'S1a: tooltip reads Bloody Strikes\' Blood Boil multiplier (tooltip_vars 1250, $boil), {pot1*boil} replaces the stale $s1. '
        'pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept '
        'from rank 1 (learn level 58); RealPointsPerLevel from rank1->covers-60-overridden '
        '(undershoot-vs-top-rank) (anchor rank 4 @ level 80); coefficient/cast_time_ms/'
        'mana_cost_pct from max rank. potency-system (PLAN P7 Death Knight pass, 2026-10-01): '
        'eff1 (SCHOOL_DAMAGE) converted to ap_potency=92.0 (deathknight-potency-report.md / '
        'deathknight-potency-proposals.txt - mismatch row, old AP-coefficient-implied potency '
        'was 14.0, the base-damage-implied 92.0 wins per the user-reviewed proposal). DieSides '
        '19 replaced by the system-standard +-5% roll.'
    ),
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Boils the blood of all enemies within $a1 yards, dealing {pot1*boil} Shadow damage.  Deals additional damage to targets infected with Blood Plague or Frost Fever.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 22, 'ImplicitTargetA_3': 22, 'ImplicitTargetB_2': 15, 'ImplicitTargetB_3': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 523, 'SpellClassMask_1': 262144, 'SpellClassSet': 15, 'SpellLevel': 24, 'SpellVisualID_1': 11117, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


obliterate_49020 = spell(
    id=49020,
    name='Obliterate',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=121, base_points=247, points_per_level=17.68421052631579, implicit_target_a=6),
        Effect(type=31, weapon_potency=79, implicit_target_a=6),
        Effect(type=EffectType.DUMMY, base_points=24, implicit_target_a=6),
    ],
    spell_icon_id=2639,
    notes=(
        'pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept '
        'from rank 1 (learn level 61); RealPointsPerLevel from rank1->top-rank-fallback (anchor '
        'rank 4 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank. '
        'potency-system (PLAN P7 Death Knight pass, 2026-10-01): eff2 (WEAPON_PERCENT_DAMAGE) '
        'converted to weapon_potency=79 (same off-by-one fix as Mangle/Swipe/Shred - '
        'base_points=79 was dealing 80% live). The flat eff1 (NORMALIZED_WEAPON_DMG) and the '
        'disease-bonus eff3 (DUMMY) are left hand-set, same reasoning as the Feral pass\'s '
        'Mangle/Swipe/Shred: far larger than weapon_potency\'s WEAPON_FLAT_BONUS_MAX=10 budget.'
    ),
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A brutal instant attack that deals $s2% weapon damage plus ${$m1*$m2/100}, total damage increased ${$m3/2}.1% per each of your diseases on the target, but consumes the diseases.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'RuneCostID': 587, 'SpellClassMask_2': 131072, 'SpellClassSet': 15, 'SpellLevel': 36, 'SpellVisualID_1': 11613, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


ferocious_dead_49038 = spell(
    id=49038,
    name='Ferocious Dead',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29999, points_per_level=1000.0, implicit_target_a=1, apply_aura=107, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=999, points_per_level=33.333333333333336, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=170,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712172, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Raise Dead lasts an additional $/1000;s1 sec,  Army of the Dead lasts an additional $/1000;s2 sec, and Death Pact grants a heal over time effect for 15 sec equal to 50% of the amount healed.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskB_1': 2048, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


improved_corpse_explosion_49601 = spell(
    id=49601,
    name='Improved Corpse Explosion',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNIC_POWER,
    mana_cost=10,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, points_per_level=0.4166666666666667, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=1737,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Exploded corpses cause $s1% additional damage.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_2': 32, 'EffectSpellClassMaskB_2': 32, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 32, 'SpellClassSet': 15},
)


# Death Strike (shared doc "Death Strike", DK0a): costs 40 Runic Power and no runes, 85% weapon damage plus 10 potency, and
# heals for 25% of the damage taken in the last 5 sec (min 5% of max health) through spell_dk_death_strike_rework
# (EFFECT_2 DUMMY, CalcValue 25 = the heal %). Percent effect first, flat effect second (U9): the core multiplies a flat
# effect that sits BEFORE the percent effect by the percent, so the flat lands whole this way. The stock script read
# Effects[EFFECT_0].DamageMultiplier (EffectChainAmplitude_1 5.0 = 5% max HP per disease); the new script ignores it and it
# is back at the default 1.0. Off-hand 66188 is untouched (no heal); the heal 45470 is declared below.
DEATH_STRIKE_WINDOW_SEC = 5
DEATH_STRIKE_MIN_HEAL_PERCENT = 5
death_strike_window_ms = const('DEATH_STRIKE_WINDOW_MS', DEATH_STRIKE_WINDOW_SEC * 1000,
                               doc='Death Strike damage record window (shared doc: the last 5 sec)')
death_strike_min_heal_pct = const('DEATH_STRIKE_MIN_HEAL_PCT', DEATH_STRIKE_MIN_HEAL_PERCENT,
                                  doc='Death Strike minimum heal, percent of maximum health')

death_strike_49998 = spell(
    id=49998,
    name='Death Strike',
    school=School.NORMAL,
    attributes=262160,
    category=1196,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNIC_POWER,
    mana_cost=400,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=85, implicit_target_a=6),
        Effect(type=EffectType.NORMALIZED_WEAPON_DMG, sp_potency=10, potency_kind='direct', time_basis_ms=1500,
               implicit_target_a=6),
        Effect(type=EffectType.DUMMY, base_points=24, implicit_target_a=6),
    ],
    spell_icon_id=2751,
    tooltip_vars=improved_death_strike_tooltip_1251,
    notes=(
        'S1a: tooltip reads Improved Death Strike (tooltip_vars 1251): $dsdmg on the damage (weapon percent and flat), $dsheal on the heal %. '
        'DK0a (death-knight-shared-rework.md "Death Strike"): PowerType 6 / ManaCost 400 (40 RP, RP x10) / RuneCostID 0 '
        '(no runes, generates none), SpellLevel 10, d0 b4 kept. Effects: eff0 WEAPON_PERCENT_DAMAGE weapon_potency 85, '
        'eff1 NORMALIZED_WEAPON_DMG sp_potency 10 direct T 1500 (percent first, flat second: U9), eff2 DUMMY base 24 -> '
        'CalcValue 25 = the heal % read by spell_dk_death_strike_rework (the stock -49998 spell_dk_death_strike is '
        'unbound). EffectChainAmplitude_1 5.0 (the stock per-disease 5% max HP) back to 1.0. AttributesEx 0x08000200 '
        'kept (0x400 would be NO_THREAT, P0 M1), AttributesEx3 1024 kept. Stock was flat eff0 bp 111 ppl 7.708 + '
        'weapon_potency 74 + DUMMY 405/37.667.'
    ),
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712172, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': f'Focuses dark power into a strike that deals ${{$s1*$<dsdmg>}}% weapon damage plus {{pot2.avg*dsdmg}} and heals you for ${{$s3*$<dsheal>}}% of all damage you have taken in the last {DEATH_STRIKE_WINDOW_SEC} sec, minimum {DEATH_STRIKE_MIN_HEAL_PERCENT}% of your maximum health.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'RangeIndex': 2, 'RuneCostID': 0, 'SpellClassMask_1': m.DEATH_STRIKE, 'SpellClassSet': 15, 'SpellLevel': 10, 'SpellPriority': 50, 'SpellVisualID_1': 11831, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
unbind_script(-49998, 'spell_dk_death_strike')  # stock key is NEGATIVE (0-verify item 4); no spell_ranks rows exist
scripted_by(death_strike_49998, 'spell_dk_death_strike_rework')


# Death Strike heal (45470), pulled from npc.csv in DK0a (WP-R M1). The shared doc says Versatility raises the heal. The stock
# row is DmgClass NONE with no spell_bonus_data row, so Unit::SpellHealingBonusDone returned the raw amount before
# DoneTotalMod (where Versatility and MOD_HEALING_DONE_PERCENT live). DefenseType 1 (magic class) plus an explicit all-zero
# spell_bonus_data row (the bonus-row branch sets the coefficient to 0) lets DoneTotalMod apply while spell power stays out.
# AttributesEx2 CANT_CRIT (0x20000000) is kept, so it never crits. The amount is set by CastCustomSpell from the damage record
# (spell_dk_death_strike_rework), so the effect is potency_excluded. No script binding on 45470 (S1's).
death_strike_heal_45470 = spell(
    id=45470,
    name='Death Strike',
    school=School.NORMAL,
    attributes=134217728,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.HEAL, base_points=629, implicit_target_a=1,
               potency_excluded='amount comes from the Death Strike damage record via CastCustomSpell '
                                '(spell_dk_death_strike_rework), not CalcValue'),
    ],
    spell_icon_id=2751,
    notes=(
        'pulled from npc.csv (DK0a, WP-R M1): DefenseType 0 -> 1 so Versatility / healing-done % apply to the Death Strike '
        'heal (shared doc), with an explicit all-zero spell_bonus_data row so spell power stays out. Everything else is the '
        'stock/live row. S1a: SpellClassMask_3 is d2 b2 (DEATH_STRIKE_HEAL, Improved Death Strike\'s SpellMod reads it) | d2 b15 '
        '(DK_SELF_HEAL, the own-healing group the Voracious capstone reads).'
    ),
    raw_overrides={'AttributesEx2': 805306368, 'AttributesEx3': 65536, 'AuraDescription_Lang_Mask': 16712172, 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A deadly attack that deals damage plus and heals the Death Knight for a percent of damage done per disease on the target.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassMask_3': m.DEATH_STRIKE_HEAL | m.DK_SELF_HEAL, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellVisualID_1': 3542},
)
bonus_coefficients(death_strike_heal_45470, direct=0.0, dot=0.0, ap=0.0, ap_dot=0.0,
                   comment='Death Knight - Death Strike heal: no spell power; DefenseType 1 only so Versatility applies')


blood_gorged_50096 = spell(
    id=50096,
    name='Blood Gorged',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=79, misc_value=127),
    ],
    spell_icon_id=24,
    notes='S1a (Blood doc "Blood Gorged", brief D6): rank 1 damage passive, stored bp 2 = +3% while above 75% health (CasterAuraState 23). The single-rank bootstrap level scaling (points_per_level 0.1333 + raw MaxLevel 80, worth ~9% at level 60) is removed. Ranks 2 / 3 are 50108 / 50109 (deathknight_blood_helpers.py).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CasterAuraState': 23, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you are above 75% health, you deal $s1% more damage.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 20971521, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


crypt_fever_50508 = spell(
    id=50508,
    name='Crypt Fever',
    school=School.NATURE,
    dispel=DispelType.DISEASE,
    mechanic=22,
    attributes=16,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, points_per_level=0.3333333333333333, implicit_target_a=6, apply_aura=284, misc_value=22, trigger_spell=65142),
    ],
    spell_icon_id=264,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx3': 1073741824, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases disease damage taken by $s1%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your diseases also cause Crypt Fever, which increases disease damage taken by the target by $s1%.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassMask_3': 16, 'SpellClassSet': 15},
)


pestilence_50842 = spell(
    id=50842,
    name='Pestilence',
    school=School.SHADOW,
    dispel=DispelType.DISEASE,
    mechanic=22,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=6),
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=47, radius_yards=5.0),
        Effect(type=77, die_sides=0, implicit_target_a=87, implicit_target_b=16, radius_yards=10.0),
    ],
    spell_icon_id=97,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 134217728, 'AttributesEx5': 4096, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Spreads existing Blood Plague and Frost Fever infections from your target to all other enemies within $a3 yards.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectRadiusIndex_2': 52, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 2, 'RuneCostID': 844, 'SpellClassMask_2': 65536, 'SpellClassSet': 15, 'SpellLevel': 20, 'SpellPriority': 50, 'SpellVisualID_1': 11172, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)
unbind_script(50842, 'spell_dk_pestilence')
scripted_by(pestilence_50842, 'spell_dk_pestilence_rework')


ebon_plague_51726 = spell(
    id=51726,
    name='Ebon Plague',
    school=School.SHADOW,
    dispel=DispelType.DISEASE,
    mechanic=22,
    attributes=262144,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=6, apply_aura=284, misc_value=22, trigger_spell=65142),
        Effect(type=EffectType.APPLY_AURA, base_points=3, points_per_level=0.15254237288135594, implicit_target_a=6, apply_aura=AuraType.DUMMY, misc_value=126),
    ],
    spell_icon_id=1933,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 136, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases disease damage taken by $s1%.\r\nIncreases magic damage taken by $s2%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Crypt Fever morphs into Ebon Plague, which increases magic damage taken by $s2% in addition to increasing disease damage taken by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712188, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassMask_2': 2048, 'SpellClassMask_3': 64, 'SpellClassSet': 15, 'SpellLevel': 1},
)


blade_barrier_51789 = spell(
    id=51789,
    name='Blade Barrier',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        Effect(type=EffectType.DUMMY, base_points=5, implicit_target_a=1),
    ],
    spell_icon_id=85,
    notes='S1a (Blood doc "Blade Barrier"): rank 1 buff, stored bp -3 = -2% damage taken, 10 s. The single-rank bootstrap level scaling (points_per_level -0.1, raw BaseLevel 20 / MaxLevel 80) is gone: it would have made the buff -7 at level 60. Rank 2 / 3 buffs are 64855 / 64856 (deathknight_blood_helpers.py).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage taken reduced.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever your Blood Runes are on cooldown, you gain Blade Barrier, reducing all damage taken by 2% for 10 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 20, 'SpellVisualID_1': 342},
)


on_a_pale_horse_51969 = spell(
    id=51969,
    name='On a Pale Horse',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, points_per_level=0.16666666666666666, implicit_target_a=1, apply_aura=211),
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=-11, misc_value=5),
    ],
    spell_icon_id=1241,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You become as hard to stop as death itself.  The duration of all Stun and Fear effects used against you is reduced by 10%, and your mounted speed is increased by 10%.  This does not stack with other movement speed increasing effects.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 67108864, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


on_a_pale_horse_51983 = spell(
    id=51983,
    name='On a Pale Horse',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, points_per_level=0.16666666666666666, implicit_target_a=1, apply_aura=172),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, points_per_level=-0.16666666666666666, implicit_target_a=1, apply_aura=232, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, points_per_level=-0.16666666666666666, implicit_target_a=1, apply_aura=232, misc_value=5),
    ],
    spell_icon_id=1241,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You become as hard to stop as death itself.  The duration of all Stun and Fear effects used against you is reduced by 10%, and your mounted speed is increased by 10%.  This does not stack with other movement speed increasing effects.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 67108864, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


will_of_the_necropolis_52284 = spell(
    id=52284,
    name='Will of the Necropolis',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, sp_potency=1.4, potency_kind='absorb', implicit_target_a=1, apply_aura=69, misc_value=127),
    ],
    spell_icon_id=857,
    notes=(
        'pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept '
        'from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ '
        'level 60); coefficient/cast_time_ms/mana_cost_pct from max rank. potency-system (PLAN '
        'P7 Death Knight pass, 2026-10-01): converted eff1 (SCHOOL_ABSORB) to sp_potency=1.4 '
        '(deathknight-potency-report.md\'s base-damage-implied default; old '
        'EffectBonusMultiplier was 0, no mismatch). Added explicit SpellLevel=0 to '
        'raw_overrides, required by the potency generator (previously implicit/absent).'
    ),
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'TEST', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'EffectBasePoints_2': -1, 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 921, 'SpellClassSet': 15, 'SpellLevel': 0},
)


plague_strike_59133 = spell(
    id=59133,
    name='Plague Strike',
    school=School.SHADOW,
    dispel=DispelType.DISEASE,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    duration_ms=12000,
    effects=[
        Effect(type=121, base_points=36, points_per_level=6.08, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, sp_potency=12.9, potency_kind='periodic', implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000, misc_value=127),
    ],
    spell_icon_id=2719,
    notes=(
        'pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept '
        'from rank 1 (learn level 55); RealPointsPerLevel from rank1->covers-60-overridden '
        '(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/'
        'mana_cost_pct from max rank. potency-system (PLAN P7 Death Knight pass, 2026-10-01): '
        'eff2 (APPLY_AURA/PERIODIC_DAMAGE, amplitude=3000) converted to sp_potency=12.9, '
        'potency_kind=\'periodic\' (deathknight-potency-report.md\'s base-damage-implied '
        'default, no mismatch). eff1 (NORMALIZED_WEAPON_DMG) is left hand-set - no sibling '
        'WEAPON_PERCENT_DAMAGE effect exists on this spell to apply weapon_potency to.'
    ),
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AttributesEx6': 4096, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Deals $o2 Shadow damage over $d.', 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A vicious strike that deals weapon damage plus $s1 modified by attack power and plagues the target, dealing $o2 Shadow damage over $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'RangeIndex': 2, 'RuneCostID': 1426, 'SpellClassMask_1': 1, 'SpellClassMask_2': 2048, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50, 'SpellVisualID_1': 11624, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


blood_gorged_61274 = spell(
    id=61274,
    name='Blood Gorged',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=280, misc_value=1),
    ],
    spell_icon_id=24,
    notes='S1a (Blood doc "Blood Gorged", brief D6): rank 1 armor penetration passive, stored bp 2 = 3%, misc 1 (physical). The bootstrap level scaling (points_per_level 0.1333 + raw MaxLevel 80) is removed. The forced class mask at SpellInfoCorrections.cpp:866 is left alone (harmless). Ranks 2 / 3 are 61275 / 61276 (deathknight_blood_helpers.py).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712188, 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 20971521, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


death_coil_62900 = spell(
    id=62900,
    name='Death Coil',
    school=School.SHADOW,
    attributes=262144,
    category=633,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNIC_POWER,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=166, points_per_level=11.04, implicit_target_a=25),
    ],
    spell_icon_id=88,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 55); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx4': 128, 'AuraDescription_Lang_Mask': 16712172, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Fire a blast of unholy energy, causing $s1 Shadow damage to an enemy target or healing ${$m1*1.5} damage from a friendly Undead target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RuneCostID': 2331, 'SpellClassMask_1': 8192, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50, 'SpellVisualID_1': 10755, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


# Threat of Thassarian off-hand copies (S2a, S2-HANDOFF U16 / U17, brief D1). Percent effect FIRST, flat effect SECOND, EFFECT_2
# empty (the stock per-disease DUMMY and its twins are gone). The numbers mirror the main hand, with the flat part split by
# school: the physical copies (66188 Death Strike, 66198 Obliterate, 66216 Plague Strike, 203322 Heart Strike) store HALF the
# main-hand flat potency, because the engine path for a physical off-hand strike doubles the flat (SpellEffects.cpp:3911) and then
# applies TOTAL_PCT 0.5 x (1 + Nerves of Cold Steel); the Frost copy 66196 is non-physical, takes neither, stores the FULL flat and
# gets its x 0.5 x (1 + Nerves) from DeathKnight::GetFrostDamageMultiplier (spell_dk_frost_offhand). Target for every off-hand
# strike = p x (weapon x percent + main-hand flat), p = 0.5 x (1 + Nerves%).
death_strike_66188 = spell(
    id=66188,
    name='Death Strike',
    school=School.NORMAL,
    attributes=2359312,
    category=1196,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=85, implicit_target_a=6),
        Effect(type=EffectType.NORMALIZED_WEAPON_DMG, sp_potency=5, potency_kind='direct', time_basis_ms=1500,
               implicit_target_a=6),
    ],
    spell_icon_id=2751,
    notes=(
        'death-knight-rework S2a (U16 / U17, brief D1): Threat of Thassarian off-hand copy of Death Strike 49998. eff0 '
        'WEAPON_PERCENT_DAMAGE weapon_potency 85 first, eff1 NORMALIZED_WEAPON_DMG sp_potency 5 (HALF of the main hand\'s 10: '
        'the physical off-hand path doubles the flat), direct T 1500; EFFECT_2 empty (the stock max-health heal DUMMY 1309 and the '
        'EffectChainAmplitude_1 5.0 are gone). SpellLevel 10 = the main hand\'s so the low-level correction matches.'
    ),
    raw_overrides={'AttributesEx': 134217728, 'AttributesEx3': 17039360, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Strikes with your off-hand weapon for $s1% weapon damage plus {pot2.avg}.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'RuneCostID': 782, 'SpellClassMask_1': 16, 'SpellClassSet': 15, 'SpellLevel': 10, 'SpellPriority': 50, 'SpellVisualID_1': 11831, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


frost_strike_66196 = spell(
    id=66196,
    name='Frost Strike',
    school=School.FROST,
    attributes=2359312,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNIC_POWER,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=60, implicit_target_a=6),
        Effect(type=EffectType.NORMALIZED_WEAPON_DMG, sp_potency=5, potency_kind='direct', time_basis_ms=1500,
               implicit_target_a=6),
    ],
    spell_icon_id=2740,
    notes=(
        'death-knight-rework S2a (U16 / U17, brief D1): Threat of Thassarian off-hand copy of Frost Strike 49143. Always Frost, '
        'so non-physical: no flat doubling and no TOTAL_PCT (SpellEffects.cpp:3897), it stores the FULL main-hand flat (sp_potency 5) '
        'and gets x 0.5 x (1 + Nerves of Cold Steel) from DeathKnight::GetFrostDamageMultiplier (spell_dk_frost_offhand). eff0 '
        'WEAPON_PERCENT_DAMAGE weapon_potency 60 first, eff1 NORMALIZED_WEAPON_DMG sp_potency 5 direct T 1500, EFFECT_2 empty (the '
        'BasePoints[E2] -1, DieSides[E2], ImplicitTargetA_3 6 and E2.d1 0x4 twins of the stock row are deleted). SpellLevel 10 = '
        'the main hand\'s.'
    ),
    raw_overrides={'AttributesEx': 134217728, 'AttributesEx3': 17039360, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly strike the enemy with your off-hand weapon for $s1% weapon damage plus {pot2.avg} as Frost damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RuneCostID': 1824, 'SpellClassMask_2': 4, 'SpellClassSet': 15, 'SpellLevel': 10, 'SpellVisualID_1': 11612, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


obliterate_66198 = spell(
    id=66198,
    name='Obliterate',
    school=School.NORMAL,
    attributes=2359312,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=72, implicit_target_a=6),
        Effect(type=EffectType.NORMALIZED_WEAPON_DMG, sp_potency=5, potency_kind='direct', time_basis_ms=1500,
               implicit_target_a=6),
    ],
    spell_icon_id=2639,
    notes=(
        'death-knight-rework S2a (U16 / U17, brief D1): Threat of Thassarian off-hand copy of Obliterate 203054. eff0 '
        'WEAPON_PERCENT_DAMAGE weapon_potency 72 first (mirrors 203054; S2 TUNE, U33; was 160), eff1 '
        'NORMALIZED_WEAPON_DMG '
        'sp_potency 5 (HALF of the main hand\'s 10: the '
        'physical off-hand path doubles the flat), direct T 1500; EFFECT_2 empty (the stock per-disease DUMMY 24 = +12.5% per '
        'disease is gone: Obliterate never reads or consumes diseases). A Killing Machine cast switches the copy to Frost through a '
        'flag the main hand sets (spell_dk_frost_offhand), and the helper adds the missing half flat back. SpellLevel 20 = the '
        'main hand\'s. d1 b17 is kept: the Killing Machine crit mod (203320) reaches the copy.'
    ),
    raw_overrides={'AttributesEx': 134217728, 'AttributesEx3': 17039360, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A brutal instant attack with your off-hand weapon that deals $s1% weapon damage plus {pot2.avg}.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RuneCostID': 2330, 'SpellClassMask_2': 131072, 'SpellClassSet': 15, 'SpellLevel': 20, 'SpellVisualID_1': 11613, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


blood_strike_66215 = spell(
    id=66215,
    name='Blood Strike',
    school=School.NORMAL,
    attributes=2359312,
    category=1207,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=121, base_points=129, points_per_level=4.2, implicit_target_a=6),
        Effect(type=31, weapon_potency=39, implicit_target_a=6),
    ],
    spell_icon_id=2624,
    notes=(
        'pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept '
        'from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 6 @ '
        'level 60); coefficient/cast_time_ms/mana_cost_pct from max rank. potency-system (PLAN '
        'P7 Death Knight pass, 2026-10-01): Threat of Thassarian off-hand copy of Blood Strike '
        '(45902). eff2 (WEAPON_PERCENT_DAMAGE) converted to weapon_potency=39 (same off-by-one '
        'fix as Mangle/Swipe/Shred - base_points=39 was dealing 40% live). The flat eff1 and '
        'the disease-bonus eff3 (free-slot constant) are left hand-set, same reasoning as '
        '45902. Added explicit SpellLevel=0 to raw_overrides, required by the potency '
        'generator (previously implicit/absent).'
    ),
    raw_overrides={'AttributesEx': 134217728, 'AttributesEx3': 17039360, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly strike the enemy, causing $s2% offhand weapon damage plus a bonus, total damage increased by ${$m3/2}.1% for each of your diseases on the target.', 'EffectBasePoints_3': 24, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RuneCostID': 1844, 'SpellClassMask_1': 4194304, 'SpellClassSet': 15, 'SpellLevel': 0, 'SpellVisualID_1': 11148, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


# Heart Strike (shared doc "Heart Strike", DK0a): baseline at level 1, 1 Blood Rune + 10 RP, 60% weapon damage plus 10
# potency to the target and half as much to the nearest other enemy; NO per-disease bonus. Percent effect first, flat
# effect second (U9). The stock per-disease bonus is read by the core (SpellEffects.cpp Heart Strike branch,
# family flag 0x1000000) from Effects[EFFECT_2].CalcValue(), so the third-slot twins (EffectBasePoints_3 9,
# EffectDieSides_3 1, ImplicitTargetA_3 25, EffectChainAmplitude_3 1.0) are deleted ON PURPOSE (brief ruling 1):
# EFFECT_2 builds all zero and the bonus is 0. SpellDescriptionVariableID 166 ($<bonus>) dropped for {pot2}.
heart_strike_55050 = spell(
    id=55050,
    name='Heart Strike',
    school=School.NORMAL,
    attributes=262160,
    category=1207,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=60, implicit_target_a=6, chain_targets=2),
        Effect(type=EffectType.NORMALIZED_WEAPON_DMG, sp_potency=10, potency_kind='direct', time_basis_ms=1500,
               implicit_target_a=6, chain_targets=2),
    ],
    spell_icon_id=3145,
    tooltip_vars=heart_plague_strike_tooltip_1254,
    notes=(
        'S2a (U24): tooltip_vars 1254 replaces 1250 so Gravefrost joins the multiplier: $heart = Bloody Strikes x Gravefrost, text unchanged. '
        'S1a: tooltip reads Bloody Strikes\' Heart Strike multiplier (tooltip_vars 1250, $heart) on the weapon percent and the flat. '
        'DK0a (death-knight-shared-rework.md "Heart Strike"): SpellLevel 1, RuneCostID 1142 (1 Blood Rune + 10 RP) kept. '
        'eff0 WEAPON_PERCENT_DAMAGE weapon_potency 60, eff1 NORMALIZED_WEAPON_DMG sp_potency 10 direct T 1500 (percent '
        'first, flat second: U9), both chain_targets 2 with EffectChainAmplitude 0.5 (the second enemy takes half). '
        'EFFECT_2 builds all zero: the stock third-slot twins (EffectBasePoints_3 9, EffectDieSides_3 1, '
        'ImplicitTargetA_3 25, EffectChainAmplitude_3 1.0) that fed the core\'s per-disease bonus are removed on '
        'purpose. Stock was flat eff0 bp 249 ppl 19.44 + weapon_potency 49 and the talent-learned SpellLevel 55.'
    ),
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx2': 4096, 'AttributesEx3': 1024, 'AttributesEx5': 32768, 'AuraDescription_Lang_Mask': 16712190, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly strike the target and the nearest other enemy, dealing ${$s1*$<heart>}% weapon damage plus {pot2.avg*heart} to the target and half as much to the second enemy.', 'EffectChainAmplitude_1': 0.5, 'EffectChainAmplitude_2': 0.5, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'RuneCostID': 1142, 'SpellClassMask_1': m.HEART_STRIKE, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellVisualID_1': 11148, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


scourge_strike_55090 = spell(
    id=55090,
    name='Scourge Strike',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=121, base_points=339, points_per_level=18.4, implicit_target_a=6),
        Effect(type=31, weapon_potency=69, implicit_target_a=6),
        Effect(type=EffectType.DUMMY, base_points=11, implicit_target_a=6),
    ],
    spell_icon_id=3143,
    notes=(
        'pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept '
        'from rank 1 (learn level 55); RealPointsPerLevel from rank1->covers-60-overridden '
        '(undershoot-vs-top-rank) (anchor rank 4 @ level 80); coefficient/cast_time_ms/'
        'mana_cost_pct from max rank. potency-system (PLAN P7 Death Knight pass, 2026-10-01): '
        'eff2 (WEAPON_PERCENT_DAMAGE) converted to weapon_potency=69 (same off-by-one fix as '
        'Mangle/Swipe/Shred - base_points=69 was dealing 70% live). The flat eff1 '
        '(NORMALIZED_WEAPON_DMG) and the disease-to-shadow-damage eff3 (DUMMY) are left '
        'hand-set, same reasoning as the Feral pass\'s Mangle/Swipe/Shred.'
    ),
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'CumulativeAura': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'An unholy strike that deals $s2% of weapon damage as Physical damage plus ${$m1*$m2/100}.  In addition, for each of your diseases on your target, you deal an additional $s3% of the Physical damage done as Shadow damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'RuneCostID': 1145, 'SpellClassMask_2': 134217728, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50, 'SpellVisualID_1': 11832, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


virulence_48962 = spell(
    id=48962,
    name='Virulence',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=55, misc_value=16),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=28),
    ],
    spell_icon_id=208,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your chance to hit with your spells by $s1% and reduces the chance that your damage over time diseases can be cured by $s2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 736225, 'EffectSpellClassMaskA_2': 1098, 'EffectSpellClassMaskB_3': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


morbidity_48963 = spell(
    id=48963,
    name='Morbidity',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=-5001, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=118,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712172, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage and healing of Death Coil by $s1% and reduces the cooldown on Death and Decay by $/1000;s2 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8192, 'EffectSpellClassMaskB_1': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


ravenous_dead_48965 = spell(
    id=48965,
    name='Ravenous Dead',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=137),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3010,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Strength by $s1% and the contribution your Ghouls get from your Strength and Stamina by $s2%.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 67108864, 'EffectSpellClassMaskB_2': 16, 'EffectSpellClassMaskC_1': 4096, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


bloody_strikes_48977 = spell(
    id=48977,
    name='Bloody Strikes',
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
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=2624,
    notes='S1a (Blood doc "Bloody Strikes"): E1 Heart Strike (A_1 d0 b24) +15 / 30 / 45%, E2 Marrowrend (B_3 d2 b8, was Blood Strike d0 b22: B_1 cleared) +10 / 20 / 30%, E3 Blood Boil (C_1 d0 b18) +10 / 20 / 30%. Masks live only in raw, keyed by effect index.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Heart Strike by 15%, your Marrowrend by 10%, and your Blood Boil by 10%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.HEART_STRIKE, 'EffectSpellClassMaskB_3': m.MARROWREND, 'EffectSpellClassMaskC_1': m.BLOOD_BOIL, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


bladed_armor_48978 = spell(
    id=48978,
    name='Bladed Armor',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=285, misc_value=1),
        Effect(type=EffectType.DUMMY),
    ],
    spell_icon_id=2653,
    notes='S1a (Blood doc "Bladed Armor"): 3 ranks. E1 aura 285 MOD_ATTACK_POWER_OF_ARMOR: attack power = armor / amount (StatSystem.cpp), stored bp 99 / 49 / 32 = amount 100 / 50 / 33, i.e. 1 / 2 / 3 attack power per 100 armor (rank 3 is really 3.03 per 100). E2 DUMMY is no longer read; the tooltip carries literal numbers.',
    raw_overrides={'AttributesEx5': 512, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your attack power by 1 for every 100 armor you have.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


butchery_48979 = spell(
    id=48979,
    name='Butchery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=10),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=85, misc_value=6),
    ],
    spell_icon_id=2664,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever you kill an enemy that grants experience or honor, you generate up to 10 Runic Power. In addition, you generate 1 Runic Power every 5 sec while in combat.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 3, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 2, 'RangeIndex': 1, 'SpellClassSet': 15},
)


improved_rune_tap_48985 = spell(
    id=48985,
    name='Improved Rune Tap',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=-10001, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=2726,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 33554432, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 6, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the health provided by Rune Tap by $s1% and lowers its cooldown by $/1000;s2 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 134217728, 'EffectSpellClassMaskB_1': 134217728, 'EquippedItemClass': -1, 'MaxLevel': 16, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 582, 'SpellClassMask_1': 262144, 'SpellClassSet': 15, 'SpellLevel': 6, 'SpellVisualID_1': 1225},
)


subversion_48997 = spell(
    id=48997,
    name='Subversion',
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
    ],
    spell_icon_id=3009,
    notes='S1a (Blood doc "Subversion"): the stock threat effect (E1, aura 107 misc 23 on d0 0x810000) is dropped, so the crit effect (aura 107 misc 7, bp 2/5/8 = 3/6/9%) is now E1 and every stock EffectSpellClassMaskB_* key was re-keyed to A_* (_masks.SUBVERSION_READ: Heart Strike d0 b24, Obliterate d1 b17, Scourge Strike d1 b27 + its d2 b7 component, Marrowrend d2 b8; Blood Strike d0 b22 gone). Stale E3 residue (ImplicitTargetA_3, C_1, EffectBonusMultiplier_3) cleared.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Heart Strike, Marrowrend, Scourge Strike and Obliterate by 3%.\n\n|cFF9D9D9DCapstone: Critical strikes from your Heart Strike, Marrowrend, Scourge Strike and Obliterate generate 5 additional Runic Power.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.SUBVERSION_READ[0], 'EffectSpellClassMaskA_2': m.SUBVERSION_READ[1], 'EffectSpellClassMaskA_3': m.SUBVERSION_READ[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


outbreak_49013 = spell(
    id=49013,
    name='Outbreak',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=97,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of Plague Strike by $s1% and Scourge Strike by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskB_2': 134217728, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 584, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50},
)


vendetta_49015 = spell(
    id=49015,
    name='Vendetta',
    school=School.SHADOW,
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
    spell_icon_id=3008,
    notes='S1a (Blood doc "Vendetta"): kill heal unchanged (E1 DUMMY bp 1 / 3 / 5 = 2 / 4 / 6%). The strike heal (5 / 10 / 15% of the damage, VENDETTA_STRIKE_HEAL_PCT_RANK1/2/3) is a const, not an effect: E2 is free. The type-2 link to the hidden proc passive 203153 is deathknight_blood_b.py\'s. Stale E2 residue (EffectBasePoints_2 -11, EffectDieSides_2, ImplicitTargetA_2/3) cleared.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals you for up to 2% of your maximum health whenever you kill a target that yields experience or honor. In addition, your Heart Strike and Marrowrend heal you for 5% of the damage they deal.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 2, 'RangeIndex': 1, 'RuneCostID': 586, 'SpellClassMask_1': 65536, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellVisualID_1': 7578},
)


sudden_doom_49018 = spell(
    id=49018,
    name='Sudden Doom',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1939,
    notes='S1a (Blood doc "Sudden Doom"): Heart Strike + Blood Boil (spell_proc -49018 family mask _masks.SUDDEN_DOOM_PROC, end of this file). Blood Boil is a magic-class spell, so ProcTypeMask 16 (DONE_SPELL_MELEE_DMG_CLASS) gains 0x10000 (DONE_SPELL_MAGIC_DMG_CLASS_NEG) = 0x10010; without it Blood Boil never reaches the aura. No internal cooldown.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712172, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Heart Strikes and Blood Boils have a 5% chance to launch a free Death Coil at your target.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 5, 'ProcTypeMask': 0x10010, 'RangeIndex': 1, 'SpellClassSet': 15},
)


might_of_mograine_49023 = spell(
    id=49023,
    name='Might of Mograine',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=2639,
    notes='S1a (Blood doc "Might of Mograine"): crit damage bonus mask _masks.MIGHT_OF_MOGRAINE_READ on E1 (Death Strike, Blood Boil, Heart Strike, Marrowrend d2 b8; Blood Strike d0 b22 dropped). Values 15 / 30 / 45% unchanged.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of your Blood Boil, Death Strike, Heart Strike and Marrowrend by 15%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.MIGHT_OF_MOGRAINE_READ[0], 'EffectSpellClassMaskA_2': m.MIGHT_OF_MOGRAINE_READ[1], 'EffectSpellClassMaskA_3': m.MIGHT_OF_MOGRAINE_READ[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


merciless_combat_49024 = _frost_rank(
    49024, 'Merciless Combat', rank=1, row=5, icon=2656,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=_TARGET_SELF, apply_aura=AuraType.DUMMY),
    ],
    description='Your Obliterate, Frost Strike and Breath of Sindragosa deal $s1% more damage to targets below 35% health.',
    notes=(
        'death-knight-rework S2a (Frost doc "Merciless Combat", U14): talent row 5, rank 1. eff0 DUMMY stored 5 = '
        '6% read by GetFrostDamageMultiplier. aura 112 / misc 7277, the d0 0x2 / d1 0x20006 mask and '
        'TargetAuraState 13 of the stock row are deleted, so the Unit.cpp 7277 hardcode (Icy Touch / Howling Blast '
        'only) goes inert.'
    ),
)


bloodworms_49027 = spell(
    id=49027,
    name='Bloodworms',
    school=School.NATURE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, die_sides=1, implicit_target_a=1, apply_aura=231, misc_value=7252, trigger_spell=50452),
    ],
    spell_icon_id=1987,
    notes='S1a (Blood doc "Bloodworms"): aura 231 value fixed at 2 (stored bp 1, die_sides 1; was 2-4 via die_sides 3), ProcChance 5 / 10 / 15, no internal cooldown (spell_proc -49027 Cooldown 0, end of this file), summon duration 18 s is 50452\'s. The talent script spell_dk_bloodworms_talent is bound on -49027.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your melee hits have a 5% chance to summon 2 Bloodworms for 18 sec. Bloodworms attack your target and heal you as they deal damage. Up to 8 Bloodworms can be active at once.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 5, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassSet': 15},
)


crypt_fever_49032 = spell(
    id=49032,
    name='Crypt Fever',
    school=School.NATURE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=112, misc_value=7282),
    ],
    spell_icon_id=264,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your diseases also cause Crypt Fever, which increases disease damage taken by the target by $50508s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


epidemic_49036 = spell(
    id=49036,
    name='Epidemic',
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
    ],
    spell_icon_id=234,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the duration of Blood Plague and Frost Fever by $/1000;s1 sec.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 100663296, 'EffectSpellClassMaskA_3': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


endless_winter_49137 = _frost_rank(
    49137, 'Endless Winter', rank=1, row=3, icon=164,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=_TARGET_SELF, apply_aura=137),
    ],
    description='Increases your Strength by $s1%.\n\n|cFF9D9D9DCapstone: Your Mind Freeze no longer costs Runic Power.|r',
    notes=(
        'death-knight-rework S2a (Frost doc "Endless Winter", D12): talent row 3, rank 1. aura 137 '
        'MOD_TOTAL_STAT_PERCENTAGE misc 0 (Strength) +2%. The stock eff1 (Mind Freeze cost, SPELLMOD_COST flat '
        '-100) is dropped entirely: only the capstone rank frees it.'
    ),
)


black_ice_49140 = _frost_rank(
    49140, 'Black Ice', rank=1, row=1, icon=154,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=48),
    ],
    description='Increases your Frost and Shadow damage by $s1%.',
    notes=(
        'death-knight-rework S2a (Frost doc "Black Ice", U23): talent row 1, 3 ranks (the stock ranks 4 / 5, 49663 '
        '/ 49664, are no longer granted). aura 79 misc 48 (Frost | Shadow) stored 1 / 3 / 5 = +2 / 4 / 6%. Aura 79 '
        'ignores class masks (Unit.cpp SpellDamageBonusDone reads misc and EquippedItemClass only), so the stock '
        'E0 class mask and the E1 / E2 twins are deleted.'
    ),
)


on_a_pale_horse_49146 = spell(
    id=49146,
    name='On a Pale Horse',
    school=School.NORMAL,
    attributes=16777616,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.LEARN_SPELL, base_points=-1, implicit_target_a=1, trigger_spell=on_a_pale_horse_51983.id),
        Effect(type=EffectType.LEARN_SPELL, base_points=-1, implicit_target_a=1, trigger_spell=on_a_pale_horse_51969.id),
    ],
    spell_icon_id=3005,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 2147614720, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You become as hard to stop as death itself.  The duration of all Stun and Fear effects used against you is reduced by 10%, and your mounted speed is increased by 10%.  This does not stack with other movement speed increasing effects.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskB_1': 67108864, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


chill_of_the_grave_49149 = _frost_rank(
    49149, 'Chill of the Grave', rank=1, row=3, icon=976,
    proc_chance=100, proc_type_mask=87056,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.PROC_TRIGGER_SPELL_WITH_VALUE, misc_value=10, trigger_spell=50480),
    ],
    masks={1: m.CHILL_OF_THE_GRAVE_PROC},
    description='Your Obliterate and Howling Blast generate 2 additional Runic Power.',
    notes=(
        'death-knight-rework S2a (Frost doc "Chill of the Grave", U19): talent row 3, rank 1. aura 231 passes its '
        'amount (20 = 2.0 Runic Power, x10 internal) to the stock energize 50480 (ENERGIZE misc 6 on the caster). '
        'The spell_proc row -49149 is declared at the end of the file as a CAST-phase proc on Obliterate + Howling '
        'Blast (m.CHILL_OF_THE_GRAVE_PROC), so it fires once per non-triggered cast with a null victim. E0 mask '
        'moved from d0 0x3 (Icy Touch / Chains of Ice) to m.CHILL_OF_THE_GRAVE_PROC; the BonusMultiplier twins are '
        'deleted. ProcTypeMask 87056 / ProcChance 100 kept.'
    ),
)


improved_icy_touch_49175 = _frost_rank(
    49175, 'Improved Icy Touch', rank=1, row=0, icon=2721,
    school=School.FROST,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=_TARGET_SELF, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=int(SpellModOp.EFFECT2)),
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=int(SpellModOp.EFFECT3)),
    ],
    masks={1: (m.ICY_TOUCH, 0, 0), 2: (0, m.FROST_FEVER_DISEASE, 0), 3: (0, m.FROST_FEVER_DISEASE, 0)},
    description=(
        'Your Icy Touch and Frost Fever deal $s1% more damage, and your Frost Fever reduces melee and ranged '
        'attack speed by an additional $s3%.\n\n|cFF9D9D9DCapstone: Increases the range of your Icy Touch, Chains '
        'of Ice and Howling Blast by 10 yards.|r'
    ),
    notes=(
        'death-knight-rework S2a (Frost doc "Improved Icy Touch", S2-HANDOFF U15 / U23): talent row 0, rank 1. '
        'eff0 is the icon-2721 DUMMY the core adds to Icy Touch (Unit.cpp SpellPctDamageModsDone, d0 0x2), stored '
        '4 / 9 / 14 = +5 / 10 / 15%. eff1 / eff2 are the stock SPELLMOD_EFFECT2 / EFFECT3 flats on Frost Fever (d1 '
        'b26) = the extra 2 / 4 / 6% attack speed slow. The Frost Fever damage part and the rank 3 range part are '
        'the type-2 linked helper 203323 (spell_linked_spell below, declared in deathknight_frost_b.py). '
        'SpellLevel 9 + 5 x 0 + rank; the stale RuneCostID / power type of the stock row and its ProcChance 50 are '
        'gone.'
    ),
)


blade_barrier_49182 = spell(
    id=49182,
    name='Blade Barrier',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=blade_barrier_51789.id),
        Effect(type=EffectType.DUMMY, base_points=5),
    ],
    spell_icon_id=85,
    notes='S1a (Blood doc "Blade Barrier"): 3 ranks of 2/4/6% (stored bp -3/-5/-7 on the talent rank E1 and on the buff row, 51789 / 64855 / 64856; live = stored + 1). Stale E3 residue (EffectBasePoints_3 -1, EffectDieSides_3, ImplicitTargetA_3, EffectSpellClassMaskC_*) cleared. Ranks 4/5 (55225 / 55226) stay declared but leave the talent.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever your Blood Runes are on cooldown, you gain Blade Barrier, reducing all damage taken by 2% for 10 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 14684919, 'EffectSpellClassMaskB_1': 12589815, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'RuneCostID': 646, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50},
)


frigid_dreadplate_49186 = spell(
    id=49186,
    name='Frigid Dreadplate',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-2, implicit_target_a=1, apply_aura=184),
    ],
    spell_icon_id=2738,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the chance melee attacks will hit you by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellPriority': 50},
)


rime_49188 = _frost_rank(
    49188, 'Rime', rank=1, row=3, icon=56,
    proc_chance=12, proc_type_mask=69904, attributes_ex3=_ATTR3_CAN_PROC_FROM_PROCS,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=_TARGET_SELF, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=59052),
    ],
    description=(
        'Your Obliterates have a $h% chance to make your next Howling Blast cost no runes and reset its '
        'cooldown.\n\n|cFF9D9D9DCapstone: Avalanche. Howling Blasts empowered by Rime also call down icicles on up '
        'to 5 enemies they hit, each dealing '
        + _AVALANCHE_POT +
        ' Frost damage.|r'
    ),
    notes=(
        'death-knight-rework S2a (Frost doc "Rime", D7 / U7): talent row 3, rank 1. ProcChance 12 (DBC; the '
        'spell_proc row -49188 has Chance 0 and inherits it, phase HIT stays). eff0 is a DUMMY: 0 on ranks 1 / 2, '
        '1 on rank 3 = the Avalanche capstone flag (the C++ gates on HasAura(59057), L4). eff1 stays '
        'PROC_TRIGGER_SPELL 59052 on EFFECT_1: spell_dk_rime registers on EFFECT_1 and resets Howling Blast\'s '
        'cooldown, moving it would lose the reset silently. The crit SpellMod (stock eff0) and its class mask are '
        'gone. ProcTypeMask 69904, AttributesEx3 and the two scripts on -49188 are kept. The capstone text quotes '
        'Avalanche 203321\'s potency through pot_text().'
    ),
)


will_of_the_necropolis_49189 = spell(
    id=49189,
    name='Will of the Necropolis',
    school=School.NORMAL,
    attributes=400,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=34, implicit_target_a=1),
        Effect(type=EffectType.LEARN_SPELL, base_points=14, implicit_target_a=1, trigger_spell=will_of_the_necropolis_52284.id),
    ],
    spell_icon_id=1762,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 2147614720, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Damage that would take you below 35% health, or that you take while below 35% health, is reduced by 5%.', 'EffectBasePoints_3': 4, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 649, 'SpellClassSet': 15},
)


unholy_blight_49194 = spell(
    id=49194,
    name='Unholy Blight',
    school=School.SHADOW,
    attributes=192,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1494,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Taking damage from a vile swarm of unholy insects.  Diseases cannot be dispelled.', 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes the victims of your Death Coil to be surrounded by a vile swarm of unholy insects, taking $49194s1% of the damage done by the Death Coil over $50536d, and preventing any diseases on the victim from being dispelled.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65536, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 55},
)


acclimation_49200 = spell(
    id=49200,
    name='Acclimation',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=10, trigger_spell=1206),
    ],
    spell_icon_id=1930,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you are hit by a spell, you have a $h% chance to boost your resistance to that type of magic for 18 sec. Stacks up to 3 times.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 3, 'EffectSpellClassMaskB_2': 536870912, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 10, 'ProcTypeMask': 131072, 'RangeIndex': 1, 'SpellClassSet': 15},
)


tundra_stalker_49202 = _frost_rank(
    49202, 'Tundra Stalker', rank=1, row=9, icon=100,
    school=School.FROST,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=_TARGET_SELF, apply_aura=AuraType.DUMMY),
    ],
    description='Your Obliterate and Breath of Sindragosa deal $s1% more damage to targets infected with your Frost Fever.',
    notes=(
        'death-knight-rework S2a (Frost doc "Tundra Stalker", U14): talent row 9, 3 ranks (50129 / 50130 are no '
        'longer granted). eff0 DUMMY stored 4 = 5% read by GetFrostDamageMultiplier (the target must carry THIS '
        'Death Knight\'s Frost Fever). aura 112 / misc 7277 with its big class mask (Unit.cpp:8443 hardcode, any '
        'Frost Fever), the expertise aura 240 (expertise is gone), the stray 30 yd range and SpellClassMask_1 of '
        '50127 / 50128 and the E2 twin are deleted.'
    ),
)


reaping_49208 = spell(
    id=49208,
    name='Reaping',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=226, amplitude=30000),
    ],
    spell_icon_id=22,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever you hit with Blood Strike or Pestilence there is a $h% chance that the Blood Rune becomes a Death Rune when it activates.  Death Runes count as a Blood, Frost or Unholy Rune.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 33, 'ProcTypeMask': 69648, 'RangeIndex': 1, 'SpellClassSet': 15},
)


wandering_plague_49217 = spell(
    id=49217,
    name='Wandering Plague',
    school=School.NATURE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=7288),
    ],
    spell_icon_id=1614,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When your diseases damage an enemy, there is a chance equal to your melee critical strike chance that they will cause $s1% additional damage to the target and all enemies within 8 yards.  Ignores any target under the effect of a spell that is cancelled by taking damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 262144, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1},
)


blood_caked_blade_49219 = spell(
    id=49219,
    name='Blood-Caked Blade',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY, trigger_spell=50463),
    ],
    spell_icon_id=138,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your auto attacks have a $h% chance to cause a Blood-Caked Strike, which hits for $50463s1% weapon damage plus ${$50463m1/2}.1% for each of your diseases on the target.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskB_1': 1024, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 10, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


dirge_49223 = spell(
    id=49223,
    name='Dirge',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=231, misc_value=10, trigger_spell=51206),
    ],
    spell_icon_id=2206,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Death Strike, Plague Strike and Scourge Strike generate 2.5 additional runic power.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4353, 'EffectSpellClassMaskA_2': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87056, 'RangeIndex': 1, 'SpellClassSet': 15},
)


magic_suppression_49224 = spell(
    id=49224,
    name='Magic Suppression',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, mechanic=26, implicit_target_a=1, apply_aura=107, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
    ],
    spell_icon_id=99,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You take $s2% less damage from all magic.  In addition, your Anti-Magic Shell absorbs an additional $s1% of spell damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'ProcCharges': 1, 'RangeIndex': 1, 'RuneCostID': 655, 'SpellClassSet': 15, 'SpellLevel': 55},
)


bladed_armor_49390 = spell(
    id=49390,
    name='Bladed Armor',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=285, misc_value=1),
        Effect(type=EffectType.DUMMY, base_points=1),
    ],
    spell_icon_id=2653,
    notes='S1a (Blood doc "Bladed Armor"): 3 ranks. E1 aura 285 MOD_ATTACK_POWER_OF_ARMOR: attack power = armor / amount (StatSystem.cpp), stored bp 99 / 49 / 32 = amount 100 / 50 / 33, i.e. 1 / 2 / 3 attack power per 100 armor (rank 3 is really 3.03 per 100). E2 DUMMY is no longer read; the tooltip carries literal numbers.',
    raw_overrides={'AttributesEx5': 512, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your attack power by 2 for every 100 armor you have.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


bladed_armor_49391 = spell(
    id=49391,
    name='Bladed Armor',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=1, apply_aura=285, misc_value=1),
        Effect(type=EffectType.DUMMY, base_points=2),
    ],
    spell_icon_id=2653,
    notes='S1a (Blood doc "Bladed Armor"): 3 ranks. E1 aura 285 MOD_ATTACK_POWER_OF_ARMOR: attack power = armor / amount (StatSystem.cpp), stored bp 99 / 49 / 32 = amount 100 / 50 / 33, i.e. 1 / 2 / 3 attack power per 100 armor (rank 3 is really 3.03 per 100). E2 DUMMY is no longer read; the tooltip carries literal numbers.',
    raw_overrides={'AttributesEx5': 512, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your attack power by 3 for every 100 armor you have.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


bladed_armor_49392 = spell(
    id=49392,
    name='Bladed Armor',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=44, implicit_target_a=1, apply_aura=285, misc_value=1),
        Effect(type=EffectType.DUMMY, base_points=3),
    ],
    spell_icon_id=2653,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx5': 512, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your attack power by $s2 for every ${$m1*$m2} armor value you have.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


bladed_armor_49393 = spell(
    id=49393,
    name='Bladed Armor',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=35, implicit_target_a=1, apply_aura=285, misc_value=1),
        Effect(type=EffectType.DUMMY, base_points=4),
    ],
    spell_icon_id=2653,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx5': 512, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your attack power by $s2 for every ${$m1*$m2} armor value you have.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


bloody_strikes_49394 = spell(
    id=49394,
    name='Bloody Strikes',
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
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=2624,
    notes='S1a (Blood doc "Bloody Strikes"): E1 Heart Strike (A_1 d0 b24) +15 / 30 / 45%, E2 Marrowrend (B_3 d2 b8, was Blood Strike d0 b22: B_1 cleared) +10 / 20 / 30%, E3 Blood Boil (C_1 d0 b18) +10 / 20 / 30%. Masks live only in raw, keyed by effect index.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Heart Strike by 30%, your Marrowrend by 20%, and your Blood Boil by 20%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.HEART_STRIKE, 'EffectSpellClassMaskB_3': m.MARROWREND, 'EffectSpellClassMaskC_1': m.BLOOD_BOIL, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


bloody_strikes_49395 = spell(
    id=49395,
    name='Bloody Strikes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=44, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=2624,
    notes='S1a (Blood doc "Bloody Strikes"): E1 Heart Strike (A_1 d0 b24) +15 / 30 / 45%, E2 Marrowrend (B_3 d2 b8, was Blood Strike d0 b22: B_1 cleared) +10 / 20 / 30%, E3 Blood Boil (C_1 d0 b18) +10 / 20 / 30%. Masks live only in raw, keyed by effect index.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Heart Strike by 45%, your Marrowrend by 30%, and your Blood Boil by 30%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.HEART_STRIKE, 'EffectSpellClassMaskB_3': m.MARROWREND, 'EffectSpellClassMaskC_1': m.BLOOD_BOIL, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


runic_power_mastery_49455 = _frost_rank(
    49455, 'Runic Power Mastery', rank=1, row=0, icon=1954,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=_TARGET_SELF, apply_aura=35,
               misc_value=6),
    ],
    description='Increases your maximum Runic Power by ${$m1/10}.',
    notes=(
        'death-knight-rework S2a (Frost doc "Runic Power Mastery", U23 / Q11): talent row 0, aura 35 '
        'MOD_INCREASE_POWER misc 6 (Runic Power, x10 internal) stored 99 / 199 = +10 / +20 Runic Power (stock +15 '
        '/ +30). The stock twins on the empty slots (E1.d0 / E1.d1 / E2.d1, BasePoints[E1] 7) and the E0 class '
        'mask are deleted.'
    ),
)


death_rune_mastery_49467 = spell(
    id=49467,
    name='Death Rune Mastery',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=226, amplitude=30000),
    ],
    spell_icon_id=2622,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712172, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever you hit with Death Strike or Obliterate there is a $h% chance that the Frost and Unholy Runes will become Death Runes when they activate.  Death Runes count as a Blood, Frost or Unholy Rune.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'ProcChance': 33, 'ProcTypeMask': 87312, 'RangeIndex': 1, 'SpellClassMask_1': 16384, 'SpellClassSet': 15, 'SpellVisualID_1': 10590},
)


glacier_rot_49471 = _frost_rank(
    49471, 'Glacier Rot', rank=1, row=4, icon=2965,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=_TARGET_SELF, apply_aura=AuraType.DUMMY),
    ],
    description=(
        'Diseased enemies take $s1% more damage from your Frost Strike, Glacial Advance and Howling '
        'Blast.\n\n|cFF9D9D9DCapstone: Your Mastery further increases the damage of Frost Strike and Glacial '
        'Advance.|r'
    ),
    notes=(
        'death-knight-rework S2a (Frost doc "Glacier Rot", U14 / D6): talent row 4, rank 1. eff0 DUMMY stored 5 = '
        '6% read by GetFrostDamageMultiplier (GetAmount of the DUMMY). Icon 2965 (Ability_Mage_ChilledToTheBone) '
        'replaces the stock 196 so the Unit.cpp Glacier Rot hardcode (GetDummyAuraEffect icon 196) goes inert; '
        'misc 7244, the E0 class mask and the BasePoints[E1] / BonusMultiplier twins are deleted. Rank 3 HasAura = '
        'the Mastery capstone.'
    ),
)


butchery_49483 = spell(
    id=49483,
    name='Butchery',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=199, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=10),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=85, misc_value=6),
    ],
    spell_icon_id=2664,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever you kill an enemy that grants experience or honor, you generate up to 20 Runic Power. In addition, you generate 2 Runic Power every 5 sec while in combat.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 3, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 2, 'RangeIndex': 1, 'SpellClassSet': 15},
)


improved_rune_tap_49488 = spell(
    id=49488,
    name='Improved Rune Tap',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=65, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=-20001, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=2726,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 33554432, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 6, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the health provided by Rune Tap by $s1% and lowers its cooldown by $/1000;s2 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 134217728, 'EffectSpellClassMaskB_1': 134217728, 'EquippedItemClass': -1, 'MaxLevel': 16, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 661, 'SpellClassMask_1': 262144, 'SpellClassSet': 15, 'SpellLevel': 6, 'SpellVisualID_1': 1225},
)


improved_rune_tap_49489 = spell(
    id=49489,
    name='Improved Rune Tap',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=-30001, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=2726,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 33554432, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 6, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the health provided by Rune Tap by $s1% and lowers its cooldown by $/1000;s2 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 134217728, 'EffectSpellClassMaskB_1': 134217728, 'EquippedItemClass': -1, 'MaxLevel': 16, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 662, 'SpellClassMask_1': 262144, 'SpellClassSet': 15, 'SpellLevel': 6, 'SpellVisualID_1': 1225},
)


subversion_49490 = spell(
    id=49490,
    name='Subversion',
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
    spell_icon_id=3009,
    notes='S1a (Blood doc "Subversion"): the stock threat effect (E1, aura 107 misc 23 on d0 0x810000) is dropped, so the crit effect (aura 107 misc 7, bp 2/5/8 = 3/6/9%) is now E1 and every stock EffectSpellClassMaskB_* key was re-keyed to A_* (_masks.SUBVERSION_READ: Heart Strike d0 b24, Obliterate d1 b17, Scourge Strike d1 b27 + its d2 b7 component, Marrowrend d2 b8; Blood Strike d0 b22 gone). Stale E3 residue (ImplicitTargetA_3, C_1, EffectBonusMultiplier_3) cleared.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Heart Strike, Marrowrend, Scourge Strike and Obliterate by 6%.\n\n|cFF9D9D9DCapstone: Critical strikes from your Heart Strike, Marrowrend, Scourge Strike and Obliterate generate 5 additional Runic Power.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.SUBVERSION_READ[0], 'EffectSpellClassMaskA_2': m.SUBVERSION_READ[1], 'EffectSpellClassMaskA_3': m.SUBVERSION_READ[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


subversion_49491 = spell(
    id=49491,
    name='Subversion',
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
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=203152),
    ],
    spell_icon_id=3009,
    notes='S1a (Blood doc "Subversion"): the stock threat effect (E1, aura 107 misc 23 on d0 0x810000) is dropped, so the crit effect (aura 107 misc 7, bp 2/5/8 = 3/6/9%) is now E1 and every stock EffectSpellClassMaskB_* key was re-keyed to A_* (_masks.SUBVERSION_READ: Heart Strike d0 b24, Obliterate d1 b17, Scourge Strike d1 b27 + its d2 b7 component, Marrowrend d2 b8; Blood Strike d0 b22 gone). Stale E3 residue (ImplicitTargetA_3, C_1, EffectBonusMultiplier_3) cleared. Rank 3 (capstone) adds E2 PROC_TRIGGER_SPELL -> 203152 (+5 Runic Power), spell_proc row below (crit hit of the four strikes, phase HIT, E1 disabled), once per cast via spell_dk_subversion_capstone.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Heart Strike, Marrowrend, Scourge Strike and Obliterate by 9%.\n\nCapstone: Critical strikes from your Heart Strike, Marrowrend, Scourge Strike and Obliterate generate 5 additional Runic Power.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.SUBVERSION_READ[0], 'EffectSpellClassMaskA_2': m.SUBVERSION_READ[1], 'EffectSpellClassMaskA_3': m.SUBVERSION_READ[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassSet': 15},
)


blade_barrier_49500 = spell(
    id=49500,
    name='Blade Barrier',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=64855),
        Effect(type=EffectType.DUMMY, base_points=5, implicit_target_a=6),
    ],
    spell_icon_id=85,
    notes='S1a (Blood doc "Blade Barrier"): 3 ranks of 2/4/6% (stored bp -3/-5/-7 on the talent rank E1 and on the buff row, 51789 / 64855 / 64856; live = stored + 1). Stale E3 residue (EffectBasePoints_3 -1, EffectDieSides_3, ImplicitTargetA_3, EffectSpellClassMaskC_*) cleared. Ranks 4/5 (55225 / 55226) stay declared but leave the talent.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever your Blood Runes are on cooldown, you gain Blade Barrier, reducing all damage taken by 4% for 10 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 14684919, 'EffectSpellClassMaskB_1': 12589815, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'RuneCostID': 663, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50},
)


blade_barrier_49501 = spell(
    id=49501,
    name='Blade Barrier',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-7, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=64856),
        Effect(type=EffectType.DUMMY, base_points=5, implicit_target_a=6),
    ],
    spell_icon_id=85,
    notes='S1a (Blood doc "Blade Barrier"): 3 ranks of 2/4/6% (stored bp -3/-5/-7 on the talent rank E1 and on the buff row, 51789 / 64855 / 64856; live = stored + 1). Stale E3 residue (EffectBasePoints_3 -1, EffectDieSides_3, ImplicitTargetA_3, EffectSpellClassMaskC_*) cleared. Ranks 4/5 (55225 / 55226) stay declared but leave the talent.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever your Blood Runes are on cooldown, you gain Blade Barrier, reducing all damage taken by 6% for 10 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 14684919, 'EffectSpellClassMaskB_1': 12589815, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'RuneCostID': 664, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50},
)


sudden_doom_49529 = spell(
    id=49529,
    name='Sudden Doom',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1939,
    notes='S1a (Blood doc "Sudden Doom"): Heart Strike + Blood Boil (spell_proc -49018 family mask _masks.SUDDEN_DOOM_PROC, end of this file). Blood Boil is a magic-class spell, so ProcTypeMask 16 (DONE_SPELL_MELEE_DMG_CLASS) gains 0x10000 (DONE_SPELL_MAGIC_DMG_CLASS_NEG) = 0x10010; without it Blood Boil never reaches the aura. No internal cooldown.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712172, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Heart Strikes and Blood Boils have a 10% chance to launch a free Death Coil at your target.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 10, 'ProcTypeMask': 0x10010, 'RangeIndex': 1, 'SpellClassSet': 15},
)


sudden_doom_49530 = spell(
    id=49530,
    name='Sudden Doom',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1939,
    notes='S1a (Blood doc "Sudden Doom"): Heart Strike + Blood Boil (spell_proc -49018 family mask _masks.SUDDEN_DOOM_PROC, end of this file). Blood Boil is a magic-class spell, so ProcTypeMask 16 (DONE_SPELL_MELEE_DMG_CLASS) gains 0x10000 (DONE_SPELL_MAGIC_DMG_CLASS_NEG) = 0x10010; without it Blood Boil never reaches the aura. No internal cooldown.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712172, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Heart Strikes and Blood Boils have a 15% chance to launch a free Death Coil at your target.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 15, 'ProcTypeMask': 0x10010, 'RangeIndex': 1, 'SpellClassSet': 15},
)


might_of_mograine_49533 = spell(
    id=49533,
    name='Might of Mograine',
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
    spell_icon_id=2639,
    notes='S1a (Blood doc "Might of Mograine"): crit damage bonus mask _masks.MIGHT_OF_MOGRAINE_READ on E1 (Death Strike, Blood Boil, Heart Strike, Marrowrend d2 b8; Blood Strike d0 b22 dropped). Values 15 / 30 / 45% unchanged.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of your Blood Boil, Death Strike, Heart Strike and Marrowrend by 30%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.MIGHT_OF_MOGRAINE_READ[0], 'EffectSpellClassMaskA_2': m.MIGHT_OF_MOGRAINE_READ[1], 'EffectSpellClassMaskA_3': m.MIGHT_OF_MOGRAINE_READ[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


might_of_mograine_49534 = spell(
    id=49534,
    name='Might of Mograine',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=44, implicit_target_a=1, apply_aura=108, misc_value=15),
    ],
    spell_icon_id=2639,
    notes='S1a (Blood doc "Might of Mograine"): crit damage bonus mask _masks.MIGHT_OF_MOGRAINE_READ on E1 (Death Strike, Blood Boil, Heart Strike, Marrowrend d2 b8; Blood Strike d0 b22 dropped). Values 15 / 30 / 45% unchanged.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike damage bonus of your Blood Boil, Death Strike, Heart Strike and Marrowrend by 45%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': m.MIGHT_OF_MOGRAINE_READ[0], 'EffectSpellClassMaskA_2': m.MIGHT_OF_MOGRAINE_READ[1], 'EffectSpellClassMaskA_3': m.MIGHT_OF_MOGRAINE_READ[2], 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


merciless_combat_49538 = _frost_rank(
    49538, 'Merciless Combat', rank=2, row=5, icon=2656,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=_TARGET_SELF, apply_aura=AuraType.DUMMY),
    ],
    description='Your Obliterate, Frost Strike and Breath of Sindragosa deal $s1% more damage to targets below 35% health.',
    notes=(
        'death-knight-rework S2a (Frost doc "Merciless Combat", U14): talent row 5, rank 2. eff0 DUMMY stored 11 = '
        '12% read by GetFrostDamageMultiplier. aura 112 / misc 7277, the d0 0x2 / d1 0x20006 mask and '
        'TargetAuraState 13 of the stock row are deleted, so the Unit.cpp 7277 hardcode (Icy Touch / Howling Blast '
        'only) goes inert.'
    ),
)


bloodworms_49542 = spell(
    id=49542,
    name='Bloodworms',
    school=School.NATURE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, die_sides=1, implicit_target_a=1, apply_aura=231, misc_value=7252, trigger_spell=50452),
    ],
    spell_icon_id=1987,
    notes='S1a (Blood doc "Bloodworms"): aura 231 value fixed at 2 (stored bp 1, die_sides 1; was 2-4 via die_sides 3), ProcChance 5 / 10 / 15, no internal cooldown (spell_proc -49027 Cooldown 0, end of this file), summon duration 18 s is 50452\'s. The talent script spell_dk_bloodworms_talent is bound on -49027.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your melee hits have a 10% chance to summon 2 Bloodworms for 18 sec. Bloodworms attack your target and heal you as they deal damage. Up to 8 Bloodworms can be active at once.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 10, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassSet': 15},
)


bloodworms_49543 = spell(
    id=49543,
    name='Bloodworms',
    school=School.NATURE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, die_sides=1, implicit_target_a=1, apply_aura=231, misc_value=7252, trigger_spell=50452),
    ],
    spell_icon_id=1987,
    notes='S1a (Blood doc "Bloodworms"): aura 231 value fixed at 2 (stored bp 1, die_sides 1; was 2-4 via die_sides 3), ProcChance 5 / 10 / 15, no internal cooldown (spell_proc -49027 Cooldown 0, end of this file), summon duration 18 s is 50452\'s. The talent script spell_dk_bloodworms_talent is bound on -49027.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your melee hits have a 15% chance to summon 2 Bloodworms for 18 sec. Bloodworms attack your target and heal you as they deal damage. Up to 8 Bloodworms can be active at once.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 15, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassSet': 15},
)


epidemic_49562 = spell(
    id=49562,
    name='Epidemic',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5999, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=234,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the duration of Blood Plague and Frost Fever by $/1000;s1 sec.', 'EffectBasePoints_3': -1, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_2': 100663296, 'EffectSpellClassMaskA_3': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


morbidity_49564 = spell(
    id=49564,
    name='Morbidity',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-10001, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=118,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712172, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage and healing of Death Coil by $s1% and reduces the cooldown on Death and Decay by $/1000;s2 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8192, 'EffectSpellClassMaskB_1': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


morbidity_49565 = spell(
    id=49565,
    name='Morbidity',
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
        Effect(type=EffectType.APPLY_AURA, base_points=-15001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=118,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712172, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage and healing of Death Coil by $s1% and reduces the cooldown on Death and Decay by $/1000;s2 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8192, 'EffectSpellClassMaskB_1': 32, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


virulence_49567 = spell(
    id=49567,
    name='Virulence',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=55, misc_value=16),
        Effect(type=EffectType.APPLY_AURA, base_points=19, apply_aura=107, misc_value=28),
    ],
    spell_icon_id=208,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your chance to hit with your spells by $s1% and reduces the chance that your damage over time diseases can be cured by $s2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 736225, 'EffectSpellClassMaskA_2': 1098, 'EffectSpellClassMaskB_3': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


virulence_49568 = spell(
    id=49568,
    name='Virulence',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=55, misc_value=16),
        Effect(type=EffectType.APPLY_AURA, base_points=29, apply_aura=107, misc_value=28),
    ],
    spell_icon_id=208,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your chance to hit with your spells by $s1% and reduces the chance that your damage over time diseases can be cured by $s2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 736225, 'EffectSpellClassMaskA_2': 1098, 'EffectSpellClassMaskB_3': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


ravenous_dead_49571 = spell(
    id=49571,
    name='Ravenous Dead',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=137),
        Effect(type=EffectType.DUMMY, base_points=39, implicit_target_a=1),
    ],
    spell_icon_id=3010,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Strength by $s1% and the contribution your Ghouls get from your Strength and Stamina by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 67108864, 'EffectSpellClassMaskB_2': 16, 'EffectSpellClassMaskC_1': 4096, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


ravenous_dead_49572 = spell(
    id=49572,
    name='Ravenous Dead',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=137),
        Effect(type=EffectType.DUMMY, base_points=59, implicit_target_a=1),
    ],
    spell_icon_id=3010,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Strength by $s1% and the contribution your Ghouls get from your Strength and Stamina by $s2%', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 67108864, 'EffectSpellClassMaskB_2': 16, 'EffectSpellClassMaskC_1': 4096, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


unholy_command_49588 = spell(
    id=49588,
    name='Unholy Command',
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
    spell_icon_id=2723,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Death Grip ability by $/1000;s1 sec.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 33554432, 'EffectSpellClassMaskB_2': 268435456, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


unholy_command_49589 = spell(
    id=49589,
    name='Unholy Command',
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
    ],
    spell_icon_id=2723,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Death Grip ability by $/1000;s1 sec.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 33554432, 'EffectSpellClassMaskB_2': 268435456, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


dirge_49599 = spell(
    id=49599,
    name='Dirge',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=231, misc_value=10, trigger_spell=51206),
    ],
    spell_icon_id=2206,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Death Strike, Plague Strike and Scourge Strike generate 5 additional runic power.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4353, 'EffectSpellClassMaskA_2': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 349200, 'RangeIndex': 1, 'SpellClassSet': 15},
)


magic_suppression_49610 = spell(
    id=49610,
    name='Magic Suppression',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=107, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
    ],
    spell_icon_id=99,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You take $s2% less damage from all magic.  In addition, your Anti-Magic Shell absorbs an additional $s1% of spell damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 690, 'SpellClassSet': 15, 'SpellLevel': 55},
)


magic_suppression_49611 = spell(
    id=49611,
    name='Magic Suppression',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, mechanic=26, implicit_target_a=1, apply_aura=107, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=-7, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
    ],
    spell_icon_id=99,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You take $s2% less damage from all magic.  In addition, your Anti-Magic Shell absorbs an additional $s1% of spell damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'ProcCharges': 1, 'RangeIndex': 1, 'RuneCostID': 691, 'SpellClassSet': 15, 'SpellLevel': 55},
)


blood_caked_blade_49627 = spell(
    id=49627,
    name='Blood-Caked Blade',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY, trigger_spell=50463),
    ],
    spell_icon_id=138,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your auto attacks have a $h% chance to cause a Blood-Caked Strike, which hits for $50463s1% weapon damage plus ${$50463m1/2}.1% for each of your diseases on the target.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskB_1': 1024, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


blood_caked_blade_49628 = spell(
    id=49628,
    name='Blood-Caked Blade',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY, trigger_spell=50463),
    ],
    spell_icon_id=138,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your auto attacks have a $h% chance to cause a Blood-Caked Strike, which hits for $50463s1% weapon damage plus ${$50463m1/2}.1% for each of your diseases on the target.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskB_1': 1024, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 30, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


crypt_fever_49631 = spell(
    id=49631,
    name='Crypt Fever',
    school=School.NATURE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=112, misc_value=7282),
    ],
    spell_icon_id=264,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your diseases also cause Crypt Fever, which increases disease damage taken by the target by $50509s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


crypt_fever_49632 = spell(
    id=49632,
    name='Crypt Fever',
    school=School.NATURE,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=112, misc_value=7282),
    ],
    spell_icon_id=264,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your diseases also cause Crypt Fever, which increases disease damage taken by the target by $50510s1%.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


wandering_plague_49654 = spell(
    id=49654,
    name='Wandering Plague',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=65, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=7288),
    ],
    spell_icon_id=1614,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When your diseases damage an enemy, there is a chance equal to your melee critical strike chance that they will cause $s1% additional damage to the target and all enemies within 8 yards.  Ignores any target under the effect of a spell that is cancelled by taking damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 262144, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1},
)


wandering_plague_49655 = spell(
    id=49655,
    name='Wandering Plague',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=7288),
    ],
    spell_icon_id=1614,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When your diseases damage an enemy, there is a chance equal to your melee critical strike chance that they will cause $s1% additional damage to the target and all enemies within 8 yards.  Ignores any target under the effect of a spell that is cancelled by taking damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 262144, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1},
)


endless_winter_49657 = _frost_rank(
    49657, 'Endless Winter', rank=2, row=3, icon=164,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=_TARGET_SELF, apply_aura=137),
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=int(SpellModOp.COST)),
    ],
    masks={2: (m.MIND_FREEZE, 0, 0)},
    description='Increases your Strength by $s1%.\n\nCapstone: Your Mind Freeze no longer costs Runic Power.',
    notes=(
        'death-knight-rework S2a (Frost doc "Endless Winter", D12): talent row 3, rank 2. aura 137 Strength +4%; '
        'eff1 aura 108 SPELLMOD_COST -100% on Mind Freeze (d0 b10, m.MIND_FREEZE), stored -101. The stale '
        'trigger_spell 55095 of the stock row, the E0 class mask and the old flat cost mod are gone.'
    ),
)


black_ice_49661 = _frost_rank(
    49661, 'Black Ice', rank=2, row=1, icon=154,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=48),
    ],
    description='Increases your Frost and Shadow damage by $s1%.',
    notes=(
        'death-knight-rework S2a (Frost doc "Black Ice", U23): talent row 1, 3 ranks (the stock ranks 4 / 5, 49663 '
        '/ 49664, are no longer granted). aura 79 misc 48 (Frost | Shadow) stored 1 / 3 / 5 = +2 / 4 / 6%. Aura 79 '
        'ignores class masks (Unit.cpp SpellDamageBonusDone reads misc and EquippedItemClass only), so the stock '
        'E0 class mask and the E1 / E2 twins are deleted.'
    ),
)


black_ice_49662 = _frost_rank(
    49662, 'Black Ice', rank=3, row=1, icon=154,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=48),
    ],
    description='Increases your Frost and Shadow damage by $s1%.',
    notes=(
        'death-knight-rework S2a (Frost doc "Black Ice", U23): talent row 1, 3 ranks (the stock ranks 4 / 5, 49663 '
        '/ 49664, are no longer granted). aura 79 misc 48 (Frost | Shadow) stored 1 / 3 / 5 = +2 / 4 / 6%. Aura 79 '
        'ignores class masks (Unit.cpp SpellDamageBonusDone reads misc and EquippedItemClass only), so the stock '
        'E0 class mask and the E1 / E2 twins are deleted.'
    ),
)


black_ice_49663 = spell(
    id=49663,
    name='Black Ice',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=79, misc_value=48),
    ],
    spell_icon_id=154,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Frost and Shadow damage by $s1%.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 2182250279, 'EffectSpellClassMaskA_2': 447, 'EffectSpellClassMaskB_1': 41975808, 'EffectSpellClassMaskB_2': 1024, 'EffectSpellClassMaskC_1': 524288, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


black_ice_49664 = spell(
    id=49664,
    name='Black Ice',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=79, misc_value=48),
    ],
    spell_icon_id=154,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Frost and Shadow damage by $s1%.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 2182250279, 'EffectSpellClassMaskA_2': 447, 'EffectSpellClassMaskB_1': 41975808, 'EffectSpellClassMaskB_2': 1024, 'EffectSpellClassMaskC_1': 524288, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


glacier_rot_49790 = _frost_rank(
    49790, 'Glacier Rot', rank=2, row=4, icon=2965,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=12, implicit_target_a=_TARGET_SELF, apply_aura=AuraType.DUMMY),
    ],
    description=(
        'Diseased enemies take $s1% more damage from your Frost Strike, Glacial Advance and Howling '
        'Blast.\n\n|cFF9D9D9DCapstone: Your Mastery further increases the damage of Frost Strike and Glacial '
        'Advance.|r'
    ),
    notes=(
        'death-knight-rework S2a (Frost doc "Glacier Rot", U14 / D6): talent row 4, rank 2. eff0 DUMMY stored 12 = '
        '13% read by GetFrostDamageMultiplier (GetAmount of the DUMMY). Icon 2965 (Ability_Mage_ChilledToTheBone) '
        'replaces the stock 196 so the Unit.cpp Glacier Rot hardcode (GetDummyAuraEffect icon 196) goes inert; '
        'misc 7244, the E0 class mask and the BasePoints[E1] / BonusMultiplier twins are deleted. Rank 3 HasAura = '
        'the Mastery capstone.'
    ),
)


glacier_rot_49791 = _frost_rank(
    49791, 'Glacier Rot', rank=3, row=4, icon=2965,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=_TARGET_SELF, apply_aura=AuraType.DUMMY),
    ],
    description=(
        'Diseased enemies take $s1% more damage from your Frost Strike, Glacial Advance and Howling '
        'Blast.\n\nCapstone: Your Mastery further increases the damage of Frost Strike and Glacial Advance.'
    ),
    notes=(
        'death-knight-rework S2a (Frost doc "Glacier Rot", U14 / D6): talent row 4, rank 3. eff0 DUMMY stored 19 = '
        '20% read by GetFrostDamageMultiplier (GetAmount of the DUMMY). Icon 2965 (Ability_Mage_ChilledToTheBone) '
        'replaces the stock 196 so the Unit.cpp Glacier Rot hardcode (GetDummyAuraEffect icon 196) goes inert; '
        'misc 7244, the E0 class mask and the BasePoints[E1] / BonusMultiplier twins are deleted. Rank 3 HasAura = '
        'the Mastery capstone.'
    ),
)


improved_icy_touch_50031 = _frost_rank(
    50031, 'Improved Icy Touch', rank=2, row=0, icon=2721,
    school=School.FROST,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=_TARGET_SELF, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=int(SpellModOp.EFFECT2)),
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=int(SpellModOp.EFFECT3)),
    ],
    masks={1: (m.ICY_TOUCH, 0, 0), 2: (0, m.FROST_FEVER_DISEASE, 0), 3: (0, m.FROST_FEVER_DISEASE, 0)},
    description=(
        'Your Icy Touch and Frost Fever deal $s1% more damage, and your Frost Fever reduces melee and ranged '
        'attack speed by an additional $s3%.\n\n|cFF9D9D9DCapstone: Increases the range of your Icy Touch, Chains '
        'of Ice and Howling Blast by 10 yards.|r'
    ),
    notes=(
        'death-knight-rework S2a (Frost doc "Improved Icy Touch", S2-HANDOFF U15 / U23): talent row 0, rank 2. '
        'eff0 is the icon-2721 DUMMY the core adds to Icy Touch (Unit.cpp SpellPctDamageModsDone, d0 0x2), stored '
        '4 / 9 / 14 = +5 / 10 / 15%. eff1 / eff2 are the stock SPELLMOD_EFFECT2 / EFFECT3 flats on Frost Fever (d1 '
        'b26) = the extra 2 / 4 / 6% attack speed slow. The Frost Fever damage part and the rank 3 range part are '
        'the type-2 linked helper 203324 (spell_linked_spell below, declared in deathknight_frost_b.py). '
        'SpellLevel 9 + 5 x 0 + rank; the stale RuneCostID / power type of the stock row and its ProcChance 50 are '
        'gone.'
    ),
)


death_rune_mastery_50033 = spell(
    id=50033,
    name='Death Rune Mastery',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=226, amplitude=30000),
    ],
    spell_icon_id=2622,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712172, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever you hit with Death Strike or Obliterate there is a $h% chance that the Frost and Unholy Runes will become Death Runes when they activate.  Death Runes count as a Blood, Frost or Unholy Rune.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 66, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassMask_1': 16384, 'SpellClassSet': 15, 'SpellVisualID_1': 10590, 'StartRecoveryTime': 1500},
)


death_rune_mastery_50034 = spell(
    id=50034,
    name='Death Rune Mastery',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=226, amplitude=30000),
    ],
    spell_icon_id=2622,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712172, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever you hit with Death Strike or Obliterate there is a $h% chance that the Frost and Unholy Runes will become Death Runes when they activate.  Death Runes count as a Blood, Frost or Unholy Rune.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassMask_1': 16384, 'SpellClassSet': 15, 'SpellVisualID_1': 10590, 'StartRecoveryTime': 1500},
)


chilblains_50040 = _frost_rank(
    50040, 'Chilblains', rank=1, row=1, icon=143,
    attributes=262352,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.ADD_TARGET_TRIGGER, misc_value=1, trigger_spell=50434),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=16),
    ],
    masks={1: (0, m.FROST_FEVER_DISEASE, 0)},
    description=(
        'Increases your Frost damage by $s2%, and victims of your Frost Fever are Chilled, reducing their movement '
        'speed by $50434s1% for $50434d.'
    ),
    notes=(
        'death-knight-rework S2a (Frost doc "Chilblains", U23): talent row 1, rank 1. eff0 aura 109 '
        'ADD_TARGET_TRIGGER keeps applying Icy Clutch 50434 to the victim of Frost Fever (d1 b26; the slow value '
        '20 / 35 / 50% and the 10 s duration live on the Icy Clutch rows, the refresh while Frost Fever ticks is '
        'spell_dk_frost_fever_chilblains). eff1 aura 79 MOD_DAMAGE_PERCENT_DONE misc 16 (Frost) +1 / 2 / 3%. The '
        'stale E1 / E2 twins (BasePoints[E1] -1, E1.d0, E2.d0 on ALL THREE ranks) are deleted: the new E1 would '
        'have inherited them (S2a-0VERIFY item 2).'
    ),
)


chilblains_50041 = _frost_rank(
    50041, 'Chilblains', rank=2, row=1, icon=143,
    attributes=262352,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.ADD_TARGET_TRIGGER, misc_value=1, trigger_spell=50435),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=16),
    ],
    masks={1: (0, m.FROST_FEVER_DISEASE, 0)},
    description=(
        'Increases your Frost damage by $s2%, and victims of your Frost Fever are Chilled, reducing their movement '
        'speed by $50435s1% for $50435d.'
    ),
    notes=(
        'death-knight-rework S2a (Frost doc "Chilblains", U23): talent row 1, rank 2. eff0 aura 109 '
        'ADD_TARGET_TRIGGER keeps applying Icy Clutch 50435 to the victim of Frost Fever (d1 b26; the slow value '
        '20 / 35 / 50% and the 10 s duration live on the Icy Clutch rows, the refresh while Frost Fever ticks is '
        'spell_dk_frost_fever_chilblains). eff1 aura 79 MOD_DAMAGE_PERCENT_DONE misc 16 (Frost) +1 / 2 / 3%. The '
        'stale E1 / E2 twins (BasePoints[E1] -1, E1.d0, E2.d0 on ALL THREE ranks) are deleted: the new E1 would '
        'have inherited them (S2a-0VERIFY item 2).'
    ),
)


chilblains_50043 = _frost_rank(
    50043, 'Chilblains', rank=3, row=1, icon=143,
    attributes=262352,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.ADD_TARGET_TRIGGER, misc_value=1, trigger_spell=50436),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=16),
    ],
    masks={1: (0, m.FROST_FEVER_DISEASE, 0)},
    description=(
        'Increases your Frost damage by $s2%, and victims of your Frost Fever are Chilled, reducing their movement '
        'speed by $50436s1% for $50436d.'
    ),
    notes=(
        'death-knight-rework S2a (Frost doc "Chilblains", U23): talent row 1, rank 3. eff0 aura 109 '
        'ADD_TARGET_TRIGGER keeps applying Icy Clutch 50436 to the victim of Frost Fever (d1 b26; the slow value '
        '20 / 35 / 50% and the 10 s duration live on the Icy Clutch rows, the refresh while Frost Fever ticks is '
        'spell_dk_frost_fever_chilblains). eff1 aura 79 MOD_DAMAGE_PERCENT_DONE misc 16 (Frost) +1 / 2 / 3%. The '
        'stale E1 / E2 twins (BasePoints[E1] -1, E1.d0, E2.d0 on ALL THREE ranks) are deleted: the new E1 would '
        'have inherited them (S2a-0VERIFY item 2).'
    ),
)


chill_of_the_grave_50115 = _frost_rank(
    50115, 'Chill of the Grave', rank=2, row=3, icon=976,
    proc_chance=100, proc_type_mask=87056,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.PROC_TRIGGER_SPELL_WITH_VALUE, misc_value=10, trigger_spell=50480),
    ],
    masks={1: m.CHILL_OF_THE_GRAVE_PROC},
    description='Your Obliterate and Howling Blast generate 5 additional Runic Power.',
    notes=(
        'death-knight-rework S2a (Frost doc "Chill of the Grave", U19): talent row 3, rank 2. aura 231 passes its '
        'amount (50 = 5.0 Runic Power, x10 internal) to the stock energize 50480 (ENERGIZE misc 6 on the caster). '
        'The spell_proc row -49149 is declared at the end of the file as a CAST-phase proc on Obliterate + Howling '
        'Blast (m.CHILL_OF_THE_GRAVE_PROC), so it fires once per non-triggered cast with a null victim. E0 mask '
        'moved from d0 0x3 (Icy Touch / Chains of Ice) to m.CHILL_OF_THE_GRAVE_PROC; the BonusMultiplier twins are '
        'deleted. ProcTypeMask 87056 / ProcChance 100 kept.'
    ),
)


rage_of_rivendare_50117 = spell(
    id=50117,
    name='Rage of Rivendare',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=112, misc_value=7293),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=240),
    ],
    spell_icon_id=2675,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spells and abilities deal 2% more damage to targets infected with Blood Plague.  Also increases your expertise by $s2.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 291774739, 'EffectSpellClassMaskA_2': 771948838, 'EffectSpellClassMaskA_3': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


rage_of_rivendare_50118 = spell(
    id=50118,
    name='Rage of Rivendare',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=112, misc_value=7293),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=240),
    ],
    spell_icon_id=2675,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spells and abilities deal 4% more damage to targets infected with Blood Plague.  Also increases your expertise by $s2.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 23339283, 'EffectSpellClassMaskA_2': 771948838, 'EffectSpellClassMaskA_3': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


rage_of_rivendare_50119 = spell(
    id=50119,
    name='Rage of Rivendare',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=112, misc_value=7293),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=240),
    ],
    spell_icon_id=2675,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spells and abilities deal 6% more damage to targets infected with Blood Plague.  Also increases your expertise by $s2.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 23339283, 'EffectSpellClassMaskA_2': 771948838, 'EffectSpellClassMaskA_3': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


rage_of_rivendare_50120 = spell(
    id=50120,
    name='Rage of Rivendare',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=112, misc_value=7293),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=240),
    ],
    spell_icon_id=2675,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spells and abilities deal 8% more damage to targets infected with Blood Plague.  Also increases your expertise by $s2.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 24387859, 'EffectSpellClassMaskA_2': 771948838, 'EffectSpellClassMaskA_3': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


rage_of_rivendare_50121 = spell(
    id=50121,
    name='Rage of Rivendare',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=112, misc_value=7293),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=240),
    ],
    spell_icon_id=2675,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spells and abilities deal 10% more damage to targets infected with Blood Plague.  Also increases your expertise by $s2.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 21242131, 'EffectSpellClassMaskA_2': 771948838, 'EffectSpellClassMaskA_3': 9, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


tundra_stalker_50127 = _frost_rank(
    50127, 'Tundra Stalker', rank=2, row=9, icon=100,
    school=School.FROST,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=_TARGET_SELF, apply_aura=AuraType.DUMMY),
    ],
    description='Your Obliterate and Breath of Sindragosa deal $s1% more damage to targets infected with your Frost Fever.',
    notes=(
        'death-knight-rework S2a (Frost doc "Tundra Stalker", U14): talent row 9, 3 ranks (50129 / 50130 are no '
        'longer granted). eff0 DUMMY stored 9 = 10% read by GetFrostDamageMultiplier (the target must carry THIS '
        'Death Knight\'s Frost Fever). aura 112 / misc 7277 with its big class mask (Unit.cpp:8443 hardcode, any '
        'Frost Fever), the expertise aura 240 (expertise is gone), the stray 30 yd range and SpellClassMask_1 of '
        '50127 / 50128 and the E2 twin are deleted.'
    ),
)


tundra_stalker_50128 = _frost_rank(
    50128, 'Tundra Stalker', rank=3, row=9, icon=100,
    school=School.FROST,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=_TARGET_SELF, apply_aura=AuraType.DUMMY),
    ],
    description='Your Obliterate and Breath of Sindragosa deal $s1% more damage to targets infected with your Frost Fever.',
    notes=(
        'death-knight-rework S2a (Frost doc "Tundra Stalker", U14): talent row 9, 3 ranks (50129 / 50130 are no '
        'longer granted). eff0 DUMMY stored 14 = 15% read by GetFrostDamageMultiplier (the target must carry THIS '
        'Death Knight\'s Frost Fever). aura 112 / misc 7277 with its big class mask (Unit.cpp:8443 hardcode, any '
        'Frost Fever), the expertise aura 240 (expertise is gone), the stray 30 yd range and SpellClassMask_1 of '
        '50127 / 50128 and the E2 twin are deleted.'
    ),
)


tundra_stalker_50129 = spell(
    id=50129,
    name='Tundra Stalker',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=112, misc_value=7277),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=240),
    ],
    spell_icon_id=100,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spells and abilities deal $s1% more damage to targets infected with Frost Fever.  Also increases your expertise by $s2.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 21242899, 'EffectSpellClassMaskA_2': 771952934, 'EffectSpellClassMaskA_3': 9, 'EffectSpellClassMaskC_2': 131074, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 131072, 'SpellClassSet': 15},
)


tundra_stalker_50130 = spell(
    id=50130,
    name='Tundra Stalker',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=112, misc_value=7277),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=240),
    ],
    spell_icon_id=100,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your spells and abilities deal $s1% more damage to targets infected with Frost Fever.  Also increases your expertise by $s2.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 21241875, 'EffectSpellClassMaskA_2': 771948838, 'EffectSpellClassMaskA_3': 9, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 131072, 'SpellClassSet': 15},
)


runic_power_mastery_50147 = _frost_rank(
    50147, 'Runic Power Mastery', rank=2, row=0, icon=1954,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=199, implicit_target_a=_TARGET_SELF, apply_aura=35,
               misc_value=6),
    ],
    description='Increases your maximum Runic Power by ${$m1/10}.',
    notes=(
        'death-knight-rework S2a (Frost doc "Runic Power Mastery", U23 / Q11): talent row 0, aura 35 '
        'MOD_INCREASE_POWER misc 6 (Runic Power, x10 internal) stored 99 / 199 = +10 / +20 Runic Power (stock +15 '
        '/ +30). The stock twins on the empty slots (E1.d0 / E1.d1 / E2.d1, BasePoints[E1] 7) and the E0 class '
        'mask are deleted.'
    ),
)


will_of_the_necropolis_50149 = spell(
    id=50149,
    name='Will of the Necropolis',
    school=School.NORMAL,
    attributes=400,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=34, implicit_target_a=1),
        Effect(type=EffectType.LEARN_SPELL, base_points=14, implicit_target_a=1, trigger_spell=52285),
    ],
    spell_icon_id=1762,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 2147614720, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Damage that would take you below 35% health, or that you take while below 35% health, is reduced by 10%.', 'EffectBasePoints_3': 4, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 801, 'SpellClassSet': 15, 'SpellLevel': 55},
)


will_of_the_necropolis_50150 = spell(
    id=50150,
    name='Will of the Necropolis',
    school=School.NORMAL,
    attributes=400,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=34, implicit_target_a=1),
        Effect(type=EffectType.LEARN_SPELL, base_points=14, implicit_target_a=1, trigger_spell=52286),
    ],
    spell_icon_id=1762,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 2147614720, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Damage that would take you below 35% health, or that you take while below 35% health, is reduced by 15%.', 'EffectBasePoints_3': 4, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 802, 'SpellClassSet': 15, 'SpellLevel': 55},
)


acclimation_50151 = spell(
    id=50151,
    name='Acclimation',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=10, trigger_spell=1206),
    ],
    spell_icon_id=1930,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you are hit by a spell, you have a $h% chance to boost your resistance to that type of magic for 18 sec. Stacks up to 3 times.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 3, 'EffectSpellClassMaskB_2': 536870912, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'ProcTypeMask': 131072, 'RangeIndex': 1, 'SpellClassSet': 15},
)


acclimation_50152 = spell(
    id=50152,
    name='Acclimation',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=10, trigger_spell=1206),
    ],
    spell_icon_id=1930,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When you are hit by a spell, you have a $h% chance to boost your resistance to that type of magic for 18 sec. Stacks up to 3 times.', 'EffectBasePoints_2': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 3, 'EffectSpellClassMaskB_2': 536870912, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 30, 'ProcTypeMask': 131072, 'RangeIndex': 1, 'SpellClassSet': 15},
)


vendetta_50154 = spell(
    id=50154,
    name='Vendetta',
    school=School.SHADOW,
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
    spell_icon_id=3008,
    notes='S1a (Blood doc "Vendetta"): kill heal unchanged (E1 DUMMY bp 1 / 3 / 5 = 2 / 4 / 6%). The strike heal (5 / 10 / 15% of the damage, VENDETTA_STRIKE_HEAL_PCT_RANK1/2/3) is a const, not an effect: E2 is free. The type-2 link to the hidden proc passive 203153 is deathknight_blood_b.py\'s.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals you for up to 4% of your maximum health whenever you kill a target that yields experience or honor. In addition, your Heart Strike and Marrowrend heal you for 10% of the damage they deal.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 2, 'RangeIndex': 1, 'RuneCostID': 803, 'SpellClassMask_1': 65536, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellVisualID_1': 7578},
)


guile_of_gorefiend_50187 = _frost_rank(
    50187, 'Guile of Gorefiend', rank=1, row=8, icon=1740,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=int(SpellModOp.CRIT_DAMAGE_BONUS)),
        Effect(type=EffectType.APPLY_AURA, base_points=1999, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=int(SpellModOp.DURATION)),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=int(SpellModOp.CRIT_DAMAGE_BONUS)),
    ],
    masks={1: m.GUILE_READ, 2: (m.ICEBOUND_FORTITUDE, 0, 0), 3: m.GUILE_HB_READ},
    description=(
        'Increases the critical strike damage bonus of your Frost Strike, Howling Blast and Obliterate by $s1%, '
        'and increases the duration of your Icebound Fortitude by $/1000;s2 sec.'
    ),
    notes=(
        'death-knight-rework S2a (Frost doc "Guile of Gorefiend", D10 / U21): talent row 8, rank 1. eff0 aura 108 '
        'SPELLMOD_CRIT_DAMAGE_BONUS +15% on Frost Strike + Obliterate (m.GUILE_READ, d1 0x20004); eff1 Icebound '
        'Fortitude duration (d0 b20) unchanged; eff2 the same op +30% on Howling Blast alone (m.GUILE_HB_READ, d1 '
        '0x2): Howling Blast is magic class, its crit excess is halved (Unit.cpp SpellCriticalDamageBonus) and '
        'Runic Focus adds +100, so +30 reaches the documented 245% total. The stale active-slot raw masks (E0.d0 '
        '0x400000 Blood Strike, E0.d1 0x20006 with Howling Blast) and the BonusMultiplier twin are deleted, '
        'otherwise Howling Blast would stack both effects (267.5%).'
    ),
)


guile_of_gorefiend_50190 = _frost_rank(
    50190, 'Guile of Gorefiend', rank=2, row=8, icon=1740,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=int(SpellModOp.CRIT_DAMAGE_BONUS)),
        Effect(type=EffectType.APPLY_AURA, base_points=3999, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=int(SpellModOp.DURATION)),
        Effect(type=EffectType.APPLY_AURA, base_points=59, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=int(SpellModOp.CRIT_DAMAGE_BONUS)),
    ],
    masks={1: m.GUILE_READ, 2: (m.ICEBOUND_FORTITUDE, 0, 0), 3: m.GUILE_HB_READ},
    description=(
        'Increases the critical strike damage bonus of your Frost Strike, Howling Blast and Obliterate by $s1%, '
        'and increases the duration of your Icebound Fortitude by $/1000;s2 sec.'
    ),
    notes=(
        'death-knight-rework S2a (Frost doc "Guile of Gorefiend", D10 / U21): talent row 8, rank 2. eff0 aura 108 '
        'SPELLMOD_CRIT_DAMAGE_BONUS +30% on Frost Strike + Obliterate (m.GUILE_READ, d1 0x20004); eff1 Icebound '
        'Fortitude duration (d0 b20) unchanged; eff2 the same op +60% on Howling Blast alone (m.GUILE_HB_READ, d1 '
        '0x2): Howling Blast is magic class, its crit excess is halved (Unit.cpp SpellCriticalDamageBonus) and '
        'Runic Focus adds +100, so +60 reaches the documented 245% total. The stale active-slot raw masks (E0.d0 '
        '0x400000 Blood Strike, E0.d1 0x20006 with Howling Blast) and the BonusMultiplier twin are deleted, '
        'otherwise Howling Blast would stack both effects (267.5%).'
    ),
)


guile_of_gorefiend_50191 = _frost_rank(
    50191, 'Guile of Gorefiend', rank=3, row=8, icon=1740,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=44, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=int(SpellModOp.CRIT_DAMAGE_BONUS)),
        Effect(type=EffectType.APPLY_AURA, base_points=5999, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=int(SpellModOp.DURATION)),
        Effect(type=EffectType.APPLY_AURA, base_points=89, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=int(SpellModOp.CRIT_DAMAGE_BONUS)),
    ],
    masks={1: m.GUILE_READ, 2: (m.ICEBOUND_FORTITUDE, 0, 0), 3: m.GUILE_HB_READ},
    description=(
        'Increases the critical strike damage bonus of your Frost Strike, Howling Blast and Obliterate by $s1%, '
        'and increases the duration of your Icebound Fortitude by $/1000;s2 sec.'
    ),
    notes=(
        'death-knight-rework S2a (Frost doc "Guile of Gorefiend", D10 / U21): talent row 8, rank 3. eff0 aura 108 '
        'SPELLMOD_CRIT_DAMAGE_BONUS +45% on Frost Strike + Obliterate (m.GUILE_READ, d1 0x20004); eff1 Icebound '
        'Fortitude duration (d0 b20) unchanged; eff2 the same op +90% on Howling Blast alone (m.GUILE_HB_READ, d1 '
        '0x2): Howling Blast is magic class, its crit excess is halved (Unit.cpp SpellCriticalDamageBonus) and '
        'Runic Focus adds +100, so +90 reaches the documented 245% total. The stale active-slot raw masks (E0.d0 '
        '0x400000 Blood Strike, E0.d1 0x20006 with Howling Blast) and the BonusMultiplier twin are deleted, '
        'otherwise Howling Blast would stack both effects (267.5%).'
    ),
)


improved_blood_presence_50365 = spell(
    id=50365,
    name='Improved Blood Presence',
    school=School.NORMAL,
    attributes=151322688,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=107, misc_value=12),
    ],
    spell_icon_id=2636,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 2147483648, 'AttributesEx3': 65536, 'AttributesEx4': 2097152, 'AuraDescription_Lang_Mask': 16712190, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While in Frost Presence or Unholy Presence, you retain $s1% healing from Blood Presence, and healing done to you is increased by $s2% in Blood Presence.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 8388608, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 332116, 'RangeIndex': 1, 'SpellClassSet': 15},
)


improved_blood_presence_50371 = spell(
    id=50371,
    name='Improved Blood Presence',
    school=School.NORMAL,
    attributes=151322688,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=12),
    ],
    spell_icon_id=2636,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 2147483648, 'AttributesEx3': 65536, 'AttributesEx4': 2097152, 'AuraDescription_Lang_Mask': 16712190, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While in Frost Presence or Unholy Presence, you retain $s1% healing from Blood Presence, and healing done to you is increased by $s2% in Blood Presence.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 8388608, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 332116, 'RangeIndex': 1, 'SpellClassSet': 15},
)


improved_frost_presence_50384 = spell(
    id=50384,
    name='Improved Frost Presence',
    school=School.NORMAL,
    attributes=151322688,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-2, implicit_target_a=1, apply_aura=107, misc_value=23),
    ],
    spell_icon_id=2632,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 2147483648, 'AttributesEx3': 65536, 'AttributesEx4': 2097152, 'AuraDescription_Lang_Mask': 16712190, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While in Blood Presence or Unholy Presence, you retain $s1% stamina from Frost Presence, and damage done to you is decreased by an additional $s2% in Frost Presence.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 32768, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


improved_frost_presence_50385 = spell(
    id=50385,
    name='Improved Frost Presence',
    school=School.NORMAL,
    attributes=151322688,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=107, misc_value=23),
    ],
    spell_icon_id=2632,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 2147483648, 'AttributesEx3': 65536, 'AttributesEx4': 2097152, 'AuraDescription_Lang_Mask': 16712190, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While in Blood Presence or Unholy Presence, you retain $s1% stamina from Frost Presence, and damage done to you is decreased by an additional $s2% in Frost Presence.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 32768, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


improved_unholy_presence_50391 = spell(
    id=50391,
    name='Improved Unholy Presence',
    school=School.NORMAL,
    attributes=151322688,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2633,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 2147483648, 'AttributesEx3': 65536, 'AttributesEx4': 2097152, 'AuraDescription_Lang_Mask': 16712190, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While in Blood Presence or Frost Presence, you retain $s1% increased movement speed from Unholy Presence, and your runes finish their cooldowns $s2% faster in Unholy Presence.', 'EffectBasePoints_2': 4, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskB_1': 256, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


improved_unholy_presence_50392 = spell(
    id=50392,
    name='Improved Unholy Presence',
    school=School.NORMAL,
    attributes=151322688,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2633,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 2147483648, 'AttributesEx3': 65536, 'AttributesEx4': 2097152, 'AuraDescription_Lang_Mask': 16712190, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While in Blood Presence or Frost Presence, you retain $s1% increased movement speed from Unholy Presence, and your runes finish their cooldowns $s2% faster in Unholy Presence.', 'EffectBasePoints_2': 9, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskB_1': 256, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


# Icy Talons capstone (user ruling 2026-10-25): the former Improved Icy Talons party/raid melee haste (hidden passive 55610,
# linked to rank 3 below). Same two-style line as every other capstone in the tree (deathknight_frost.py _capstone_text).
_ICY_TALONS_CAPSTONE = (
    'Increases the melee attack speed of all party and raid members within $55610a1 yards by $55610s1%.'
)
_ICY_TALONS_CAPSTONE_LAST = f'\n\nCapstone: {_ICY_TALONS_CAPSTONE}'
_ICY_TALONS_CAPSTONE_GREY = f'\n\n|cFF9D9D9DCapstone: {_ICY_TALONS_CAPSTONE}|r'


icy_talons_50880 = _frost_rank(
    50880, 'Icy Talons', rank=1, row=2, icon=3785,
    school=School.FROST, attributes=448, proc_chance=100, proc_type_mask=69648,
    attributes_ex3=_ATTR3_CAN_PROC_FROM_PROCS, class_mask_1=2,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.PROC_TRIGGER_SPELL_WITH_VALUE, trigger_spell=50882),
        Effect(type=EffectType.DUMMY, base_points=2),
    ],
    masks={1: (m.ICY_TOUCH, 0, 0), 2: (0xC01AF7, 0, 0)},
    description=(
        'You leech heat from victims of your Frost Fever, so that when their melee attack speed is reduced, yours '
        'increases by $s2% for the next 20 sec.' + _ICY_TALONS_CAPSTONE_GREY
    ),
    notes=(
        'death-knight-rework S2a (Frost doc "Icy Talons", U23): talent row 2, 3 ranks (50886 / 50887 are no longer '
        'granted). eff0 aura 231 passes its amount to the buff 50882 (SPELLVALUE_BASE_POINT0), so stored 2 = 3% '
        'here and on the buff (buff rows are deleted from npc.csv and owned by deathknight_frost_helpers.py). eff1 '
        'DUMMY is the tooltip value. The stock -50880 spell_proc row (Frost Fever, TRIGGERED_CAN_PROC) is kept. '
        'The E2 twins (BasePoints[E2] -1, E2.d0) are deleted; the stock own class mask 0x2 stays (a d0 b1 '
        'collision accepted by S2-HANDOFF section 5).'
    ),
)


icy_talons_50884 = _frost_rank(
    50884, 'Icy Talons', rank=2, row=2, icon=3785,
    school=School.FROST, attributes=448, proc_chance=100, proc_type_mask=69648,
    attributes_ex3=_ATTR3_CAN_PROC_FROM_PROCS, class_mask_1=2,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.PROC_TRIGGER_SPELL_WITH_VALUE, trigger_spell=58575),
        Effect(type=EffectType.DUMMY, base_points=5),
    ],
    masks={1: (m.ICY_TOUCH, 0, 0), 2: (0xC01AF7, 0, 0)},
    description=(
        'You leech heat from victims of your Frost Fever, so that when their melee attack speed is reduced, yours '
        'increases by $s2% for the next 20 sec.' + _ICY_TALONS_CAPSTONE_GREY
    ),
    notes=(
        'death-knight-rework S2a (Frost doc "Icy Talons", U23): talent row 2, 3 ranks (50886 / 50887 are no longer '
        'granted). eff0 aura 231 passes its amount to the buff 58575 (SPELLVALUE_BASE_POINT0), so stored 5 = 6% '
        'here and on the buff (buff rows are deleted from npc.csv and owned by deathknight_frost_helpers.py). eff1 '
        'DUMMY is the tooltip value. The stock -50880 spell_proc row (Frost Fever, TRIGGERED_CAN_PROC) is kept. '
        'The E2 twins (BasePoints[E2] -1, E2.d0) are deleted; the stock own class mask 0x2 stays (a d0 b1 '
        'collision accepted by S2-HANDOFF section 5).'
    ),
)


icy_talons_50885 = _frost_rank(
    50885, 'Icy Talons', rank=3, row=2, icon=3785,
    school=School.FROST, attributes=448, proc_chance=100, proc_type_mask=69648,
    attributes_ex3=_ATTR3_CAN_PROC_FROM_PROCS, class_mask_1=2,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.PROC_TRIGGER_SPELL_WITH_VALUE, trigger_spell=58576),
        Effect(type=EffectType.DUMMY, base_points=9),
    ],
    masks={1: (m.ICY_TOUCH, 0, 0), 2: (0xC01AF7, 0, 0)},
    description=(
        'You leech heat from victims of your Frost Fever, so that when their melee attack speed is reduced, yours '
        'increases by $s2% for the next 20 sec.' + _ICY_TALONS_CAPSTONE_LAST
    ),
    notes=(
        'death-knight-rework S2a (Frost doc "Icy Talons", U23): talent row 2, 3 ranks (50886 / 50887 are no longer '
        'granted). eff0 aura 231 passes its amount to the buff 58576 (SPELLVALUE_BASE_POINT0), so stored 9 = 10% '
        'here and on the buff (buff rows are deleted from npc.csv and owned by deathknight_frost_helpers.py). eff1 '
        'DUMMY is the tooltip value. The stock -50880 spell_proc row (Frost Fever, TRIGGERED_CAN_PROC) is kept. '
        'The E2 twins (BasePoints[E2] -1, E2.d0) are deleted; the stock own class mask 0x2 stays (a d0 b1 '
        'collision accepted by S2-HANDOFF section 5). Rank 3 is the capstone: the type-2 spell_linked_spell row '
        'below adds and removes the hidden party aura 55610 with it (ex Improved Icy Talons, user ruling '
        '2026-10-25).'
    ),
)


icy_talons_50886 = spell(
    id=50886,
    name='Icy Talons',
    school=School.FROST,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=20.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=231, trigger_spell=58577),
        Effect(type=EffectType.DUMMY, base_points=15),
    ],
    spell_icon_id=3785,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You leech heat from victims of your Frost Fever, so that when their melee attack speed is reduced, yours increases by $s2% for the next 20 sec.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 2, 'EffectSpellClassMaskB_1': 12589815, 'EffectSpellClassMaskC_1': 4194437, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 4112, 'RuneCostID': 849, 'SpellClassMask_1': 2, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50},
)


icy_talons_50887 = spell(
    id=50887,
    name='Icy Talons',
    school=School.FROST,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=20.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=231, trigger_spell=58578),
        Effect(type=EffectType.DUMMY, base_points=19),
    ],
    spell_icon_id=3785,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You leech heat from victims of your Frost Fever, so that when their melee attack speed is reduced, yours increases by $s2% for the next 20 sec.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 2, 'EffectSpellClassMaskB_1': 12589815, 'EffectSpellClassMaskC_1': 4194437, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 4112, 'RuneCostID': 850, 'SpellClassMask_1': 2, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50},
)


ebon_plaguebringer_51099 = spell(
    id=51099,
    name='Ebon Plaguebringer',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=112, misc_value=7282),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=52, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=57),
    ],
    spell_icon_id=1766,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Crypt Fever morphs into Ebon Plague, which increases magic damage taken by 4% in addition to increasing disease damage taken.  Improves your critical strike chance with weapons and spells by $51099s2% at all times.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


frigid_dreadplate_51108 = spell(
    id=51108,
    name='Frigid Dreadplate',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=184, misc_value=1),
    ],
    spell_icon_id=2738,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the chance melee attacks will hit you by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 40, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellPriority': 50},
)


frigid_dreadplate_51109 = spell(
    id=51109,
    name='Frigid Dreadplate',
    school=School.FROST,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-4, implicit_target_a=1, apply_aura=184, misc_value=1),
    ],
    spell_icon_id=2738,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the chance melee attacks will hit you by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 40, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellPriority': 50},
)


killing_machine_51123 = _frost_rank(
    51123, 'Killing Machine', rank=1, row=3, icon=2702,
    proc_chance=100, proc_type_mask=4, attributes_ex3=_ATTR3_CAN_PROC_FROM_PROCS,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=_TARGET_SELF, apply_aura=AuraType.PROC_TRIGGER_SPELL,
               trigger_spell=203320),
    ],
    description=(
        'Your auto attacks have a 3% chance to make your next Obliterate a critical strike that deals Frost '
        'damage. The chance is doubled while you wield a two-handed weapon. Stacks up to 2 times.'
    ),
    notes=(
        'death-knight-rework S2a (Frost doc "Killing Machine", D8 / U6): talent row 3, 3 ranks (51129 / 51130 are '
        'no longer granted and lose their spell_proc rows). eff0 triggers the new buff 203320 (Killing Machine, 2 '
        'stacks, 30 s) instead of the stock 51124. The spell_proc rows are declared per rank at the end of the '
        'file (Chance 6 = the two-hander value, the script spell_dk_killing_machine_talent halves it for a '
        'one-hander; the displayed 3% is the one-hander value). ProcChance / ProcTypeMask 4 (auto attack) and '
        'AttributesEx3 CAN_PROC_FROM_PROCS kept.'
    ),
)


killing_machine_51127 = _frost_rank(
    51127, 'Killing Machine', rank=2, row=3, icon=2702,
    proc_chance=100, proc_type_mask=4, attributes_ex3=_ATTR3_CAN_PROC_FROM_PROCS,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=_TARGET_SELF, apply_aura=AuraType.PROC_TRIGGER_SPELL,
               trigger_spell=203320),
    ],
    description=(
        'Your auto attacks have a 6% chance to make your next Obliterate a critical strike that deals Frost '
        'damage. The chance is doubled while you wield a two-handed weapon. Stacks up to 2 times.'
    ),
    notes=(
        'death-knight-rework S2a (Frost doc "Killing Machine", D8 / U6): talent row 3, 3 ranks (51129 / 51130 are '
        'no longer granted and lose their spell_proc rows). eff0 triggers the new buff 203320 (Killing Machine, 2 '
        'stacks, 30 s) instead of the stock 51124. The spell_proc rows are declared per rank at the end of the '
        'file (Chance 12 = the two-hander value, the script spell_dk_killing_machine_talent halves it for a '
        'one-hander; the displayed 6% is the one-hander value). ProcChance / ProcTypeMask 4 (auto attack) and '
        'AttributesEx3 CAN_PROC_FROM_PROCS kept.'
    ),
)


killing_machine_51128 = _frost_rank(
    51128, 'Killing Machine', rank=3, row=3, icon=2702,
    proc_chance=100, proc_type_mask=4, attributes_ex3=_ATTR3_CAN_PROC_FROM_PROCS,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=_TARGET_SELF, apply_aura=AuraType.PROC_TRIGGER_SPELL,
               trigger_spell=203320),
    ],
    description=(
        'Your auto attacks have a 10% chance to make your next Obliterate a critical strike that deals Frost '
        'damage. The chance is doubled while you wield a two-handed weapon. Stacks up to 2 times.'
    ),
    notes=(
        'death-knight-rework S2a (Frost doc "Killing Machine", D8 / U6): talent row 3, 3 ranks (51129 / 51130 are '
        'no longer granted and lose their spell_proc rows). eff0 triggers the new buff 203320 (Killing Machine, 2 '
        'stacks, 30 s) instead of the stock 51124. The spell_proc rows are declared per rank at the end of the '
        'file (Chance 20 = the two-hander value, the script spell_dk_killing_machine_talent halves it for a '
        'one-hander; the displayed 10% is the one-hander value). ProcChance / ProcTypeMask 4 (auto attack) and '
        'AttributesEx3 CAN_PROC_FROM_PROCS kept.'
    ),
)


killing_machine_51129 = spell(
    id=51129,
    name='Killing Machine',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=51124),
    ],
    spell_icon_id=2702,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your melee attacks have a chance to make your next Icy Touch, Howling Blast or Frost Strike a critical strike.  Effect occurs more often than Killing Machine (Rank 3).', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 0, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


killing_machine_51130 = spell(
    id=51130,
    name='Killing Machine',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=51124),
    ],
    spell_icon_id=2702,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your melee attacks have a chance to make your next Icy Touch, Howling Blast or Frost Strike a critical strike.  Effect occurs more often than Killing Machine (Rank 4).', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 0, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


ebon_plaguebringer_51160 = spell(
    id=51160,
    name='Ebon Plaguebringer',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=112, misc_value=7282),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=52),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=57),
    ],
    spell_icon_id=1766,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Crypt Fever morphs into Ebon Plague, which increases magic damage taken by 9% in addition to increasing disease damage taken.  Improves your critical strike chance with weapons and spells by $51160s2% at all times.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


ebon_plaguebringer_51161 = spell(
    id=51161,
    name='Ebon Plaguebringer',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=112, misc_value=7282),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=52),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=57),
    ],
    spell_icon_id=1766,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Crypt Fever morphs into Ebon Plague, which increases magic damage taken by 13% in addition to increasing disease damage taken.  Improves your critical strike chance with weapons and spells by $51161s2% at all times.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


on_a_pale_horse_51267 = spell(
    id=51267,
    name='On a Pale Horse',
    school=School.NORMAL,
    attributes=16777616,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.LEARN_SPELL, base_points=-1, implicit_target_a=1, trigger_spell=51986),
        Effect(type=EffectType.LEARN_SPELL, base_points=-1, implicit_target_a=1, trigger_spell=51970),
    ],
    spell_icon_id=3005,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 2147614720, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You become as hard to stop as death itself.  The duration of all Stun and Fear effects used against you is reduced by 20%, and your mounted speed is increased by 20%.  This does not stack with other movement speed increasing effects.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskB_1': 67108864, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


improved_icy_touch_51456 = _frost_rank(
    51456, 'Improved Icy Touch', rank=3, row=0, icon=2721,
    school=School.FROST,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=_TARGET_SELF, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-7, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=int(SpellModOp.EFFECT2)),
        Effect(type=EffectType.APPLY_AURA, base_points=-7, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=int(SpellModOp.EFFECT3)),
    ],
    masks={1: (m.ICY_TOUCH, 0, 0), 2: (0, m.FROST_FEVER_DISEASE, 0), 3: (0, m.FROST_FEVER_DISEASE, 0)},
    description=(
        'Your Icy Touch and Frost Fever deal $s1% more damage, and your Frost Fever reduces melee and ranged '
        'attack speed by an additional $s3%.\n\nCapstone: Increases the range of your Icy Touch, Chains of Ice and '
        'Howling Blast by 10 yards.'
    ),
    notes=(
        'death-knight-rework S2a (Frost doc "Improved Icy Touch", S2-HANDOFF U15 / U23): talent row 0, rank 3. '
        'eff0 is the icon-2721 DUMMY the core adds to Icy Touch (Unit.cpp SpellPctDamageModsDone, d0 0x2), stored '
        '4 / 9 / 14 = +5 / 10 / 15%. eff1 / eff2 are the stock SPELLMOD_EFFECT2 / EFFECT3 flats on Frost Fever (d1 '
        'b26) = the extra 2 / 4 / 6% attack speed slow. The Frost Fever damage part and the rank 3 range part are '
        'the type-2 linked helper 203325 (spell_linked_spell below, declared in deathknight_frost_b.py). '
        'SpellLevel 9 + 5 x 0 + rank; the stale RuneCostID / power type of the stock row and its ProcChance 50 are '
        'gone.'
    ),
)


necrosis_51459 = spell(
    id=51459,
    name='Necrosis',
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
    spell_icon_id=2709,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your auto attacks deal an additional $s1% Shadow damage.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskB_1': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


necrosis_51462 = spell(
    id=51462,
    name='Necrosis',
    school=School.SHADOW,
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
    spell_icon_id=2709,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your auto attacks deal an additional $s1% Shadow damage.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskB_1': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


necrosis_51463 = spell(
    id=51463,
    name='Necrosis',
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
    spell_icon_id=2709,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your auto attacks deal an additional $s1% Shadow damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


necrosis_51464 = spell(
    id=51464,
    name='Necrosis',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2709,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your auto attacks deal an additional $s1% Shadow damage.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskB_1': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


necrosis_51465 = spell(
    id=51465,
    name='Necrosis',
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
    spell_icon_id=2709,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your auto attacks deal an additional $s1% Shadow damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 1024, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


annihilation_51468 = _frost_rank(
    51468, 'Annihilation', rank=1, row=2, icon=2710,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=_TARGET_SELF, apply_aura=AuraType.MOD_CRIT_PCT),
    ],
    description='Increases your critical strike chance by $s1%.',
    notes=(
        'death-knight-rework S2a (Frost doc "Annihilation", D13): talent row 2. eff0 is aura 290 MOD_CRIT_PCT +1 / '
        '2 / 3% (all crit), so GetDummyAuraEffect(DK, 2710, EFFECT_0) no longer finds a DUMMY here and Obliterate '
        '203054 is guarded by 203055 alone (first match, Unit.cpp). The stock DUMMY, the crit SpellMod on its '
        'class mask and every raw mask / twin are deleted. Icon 2710 kept (talent icon).'
    ),
)


annihilation_51472 = _frost_rank(
    51472, 'Annihilation', rank=2, row=2, icon=2710,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.MOD_CRIT_PCT),
    ],
    description='Increases your critical strike chance by $s1%.',
    notes=(
        'death-knight-rework S2a (Frost doc "Annihilation", D13): talent row 2. eff0 is aura 290 MOD_CRIT_PCT +1 / '
        '2 / 3% (all crit), so GetDummyAuraEffect(DK, 2710, EFFECT_0) no longer finds a DUMMY here and Obliterate '
        '203054 is guarded by 203055 alone (first match, Unit.cpp). The stock DUMMY, the crit SpellMod on its '
        'class mask and every raw mask / twin are deleted. Icon 2710 kept (talent icon).'
    ),
)


annihilation_51473 = _frost_rank(
    51473, 'Annihilation', rank=3, row=2, icon=2710,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.MOD_CRIT_PCT),
    ],
    description='Increases your critical strike chance by $s1%.',
    notes=(
        'death-knight-rework S2a (Frost doc "Annihilation", D13): talent row 2. eff0 is aura 290 MOD_CRIT_PCT +1 / '
        '2 / 3% (all crit), so GetDummyAuraEffect(DK, 2710, EFFECT_0) no longer finds a DUMMY here and Obliterate '
        '203054 is guarded by 203055 alone (first match, Unit.cpp). The stock DUMMY, the crit SpellMod on its '
        'class mask and every raw mask / twin are deleted. Icon 2710 kept (talent icon).'
    ),
)


vicious_strikes_51745 = spell(
    id=51745,
    name='Vicious Strikes',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108, misc_value=15),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=2623,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance by $s2% and critical strike damage bonus by $s1% of your Plague Strike and Scourge Strike.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskA_2': 134217728, 'EffectSpellClassMaskA_3': 128, 'EffectSpellClassMaskB_1': 17, 'EffectSpellClassMaskB_2': 134217728, 'EffectSpellClassMaskB_3': 128, 'EffectSpellClassMaskC_1': 4194305, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


vicious_strikes_51746 = spell(
    id=51746,
    name='Vicious Strikes',
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
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=2623,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance by $s2% and critical strike damage bonus by $s1% of your Plague Strike and Scourge Strike.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskA_2': 134217728, 'EffectSpellClassMaskA_3': 128, 'EffectSpellClassMaskB_1': 17, 'EffectSpellClassMaskB_2': 134217728, 'EffectSpellClassMaskB_3': 128, 'EffectSpellClassMaskC_1': 4194305, 'EquippedItemClass': -1, 'ImplicitTargetA_3': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


master_of_ghouls_52143 = spell(
    id=52143,
    name='Master of Ghouls',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNIC_POWER,
    mana_cost=10,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-60001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=221,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown on Raise Dead by ${$m1/-1000} sec, and the Ghoul summoned by your Raise Dead spell is considered a pet under your control.  Unlike normal Death Knight Ghouls, your pet does not have a limited duration.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskB_2': 32, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


abomination_s_might_53137 = spell(
    id=53137,
    name="Abomination's Might",
    school=School.NORMAL,
    attributes=80,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=65, base_points=4, implicit_target_a=1, apply_aura=166, radius_yards=40.0),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=137),
        Effect(type=65, base_points=4, implicit_target_a=1, apply_aura=167, radius_yards=40.0),
    ],
    spell_icon_id=2729,
    notes='S1a (Blood doc "Abomination\'s Might"): area aura radius 100 -> 40 yd on E1 (AP) and E3 (ranged AP). Values unchanged (AP 5 / 10%, Strength 1 / 2%).',
    raw_overrides={'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Attack power increased.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the attack power of party and raid members within 40 yards by 5%. Also increases your total Strength by 1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassSet': 15},
)


abomination_s_might_53138 = spell(
    id=53138,
    name="Abomination's Might",
    school=School.NORMAL,
    attributes=80,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=65, base_points=9, implicit_target_a=1, apply_aura=166, radius_yards=40.0),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=137),
        Effect(type=65, base_points=9, implicit_target_a=1, apply_aura=167, radius_yards=40.0),
    ],
    spell_icon_id=2729,
    notes='S1a (Blood doc "Abomination\'s Might"): area aura radius 100 -> 40 yd on E1 (AP) and E3 (ranged AP). Values unchanged (AP 5 / 10%, Strength 1 / 2%).',
    raw_overrides={'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Attack power increased.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the attack power of party and raid members within 40 yards by 10%. Also increases your total Strength by 2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassSet': 15},
)


blood_of_the_north_54637 = _frost_rank(
    54637, 'Blood of the North', rank=3, row=7, icon=3041,
    school=School.SHADOW, attributes=448, proc_chance=101, proc_type_mask=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=int(SpellModOp.DAMAGE)),
    ],
    masks={1: (0, m.OBLITERATE, 0)},
    description='Increases the damage of your Obliterate by $s1%.',
    notes=(
        'death-knight-rework S2a (Frost doc "Blood of the North", D9 / U15): talent row 7, rank 3. eff0 aura 108 '
        'SPELLMOD_DAMAGE +15% on Obliterate (d1 b17). The stock PERIODIC_DUMMY (icon 3041 traps, Death Rune '
        'conversion) and the Blood Strike / Frost Strike mask are gone. ProcTypeMask 0 so no default spell_proc '
        'row is rebuilt from the DBC flags; remove_spell_proc(-54639) and unbind_script(-54639, '
        '\'spell_dk_death_rune\') are declared at the end of the file (the name stays bound to -49208 / -49467).'
    ),
)


blood_of_the_north_54638 = _frost_rank(
    54638, 'Blood of the North', rank=2, row=7, icon=3041,
    school=School.SHADOW, attributes=464, proc_chance=101, proc_type_mask=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=int(SpellModOp.DAMAGE)),
    ],
    masks={1: (0, m.OBLITERATE, 0)},
    description='Increases the damage of your Obliterate by $s1%.',
    notes=(
        'death-knight-rework S2a (Frost doc "Blood of the North", D9 / U15): talent row 7, rank 2. eff0 aura 108 '
        'SPELLMOD_DAMAGE +10% on Obliterate (d1 b17). The stock PERIODIC_DUMMY (icon 3041 traps, Death Rune '
        'conversion) and the Blood Strike / Frost Strike mask are gone. ProcTypeMask 0 so no default spell_proc '
        'row is rebuilt from the DBC flags; remove_spell_proc(-54639) and unbind_script(-54639, '
        '\'spell_dk_death_rune\') are declared at the end of the file (the name stays bound to -49208 / -49467).'
    ),
)


blood_of_the_north_54639 = _frost_rank(
    54639, 'Blood of the North', rank=1, row=7, icon=3041,
    school=School.SHADOW, attributes=464, proc_chance=101, proc_type_mask=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=int(SpellModOp.DAMAGE)),
    ],
    masks={1: (0, m.OBLITERATE, 0)},
    description='Increases the damage of your Obliterate by $s1%.',
    notes=(
        'death-knight-rework S2a (Frost doc "Blood of the North", D9 / U15): talent row 7, rank 1. eff0 aura 108 '
        'SPELLMOD_DAMAGE +5% on Obliterate (d1 b17). The stock PERIODIC_DUMMY (icon 3041 traps, Death Rune '
        'conversion) and the Blood Strike / Frost Strike mask are gone. ProcTypeMask 0 so no default spell_proc '
        'row is rebuilt from the DBC flags; remove_spell_proc(-54639) and unbind_script(-54639, '
        '\'spell_dk_death_rune\') are declared at the end of the file (the name stays bound to -49208 / -49467).'
    ),
)


icy_reach_55061 = spell(
    id=55061,
    name='Icy Reach',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=107, misc_value=5),
    ],
    spell_icon_id=36,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of your Icy Touch,  Chains of Ice and Howling Blast by $s1 yards.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 6, 'EffectSpellClassMaskA_2': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


icy_reach_55062 = spell(
    id=55062,
    name='Icy Reach',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=5),
    ],
    spell_icon_id=36,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of your Icy Touch, Chains of Ice and Howling Blast by $s1 yards.', 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 6, 'EffectSpellClassMaskA_2': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


vendetta_55136 = spell(
    id=55136,
    name='Vendetta',
    school=School.SHADOW,
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
    spell_icon_id=3008,
    notes='S1a (Blood doc "Vendetta"): kill heal unchanged (E1 DUMMY bp 1 / 3 / 5 = 2 / 4 / 6%). The strike heal (5 / 10 / 15% of the damage, VENDETTA_STRIKE_HEAL_PCT_RANK1/2/3) is a const, not an effect: E2 is free. The type-2 link to the hidden proc passive 203153 is deathknight_blood_b.py\'s.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals you for up to 6% of your maximum health whenever you kill a target that yields experience or honor. In addition, your Heart Strike and Marrowrend heal you for 15% of the damage they deal.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 2, 'RangeIndex': 1, 'RuneCostID': 1147, 'SpellClassMask_1': 65536, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellVisualID_1': 7578},
)


blade_barrier_55225 = spell(
    id=55225,
    name='Blade Barrier',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=64858),
        Effect(type=EffectType.DUMMY, base_points=5, implicit_target_a=6),
    ],
    spell_icon_id=85,
    notes='S1a: leaves the Blade Barrier talent (3 ranks now); the row stays declared, only the stale E3 residue is cleared. Its buff trigger 64858 / 64859 is orphaned.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever your Blood Runes are on cooldown, you gain the Blade Barrier effect, which decreases damage taken by $64858s1% for the next $64858d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 14684919, 'EffectSpellClassMaskB_1': 12589815, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'RuneCostID': 1164, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50},
)


blade_barrier_55226 = spell(
    id=55226,
    name='Blade Barrier',
    school=School.NORMAL,
    attributes=448,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-6, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=64859),
        Effect(type=EffectType.DUMMY, base_points=5, implicit_target_a=6),
    ],
    spell_icon_id=85,
    notes='S1a: leaves the Blade Barrier talent (3 ranks now); the row stays declared, only the stale E3 residue is cleared. Its buff trigger 64858 / 64859 is orphaned.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever your Blood Runes are on cooldown, you gain the Blade Barrier effect, which decreases damage taken by $64859s1% for the next $64859d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 14684919, 'EffectSpellClassMaskB_1': 12589815, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'RuneCostID': 1165, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50},
)


outbreak_55236 = spell(
    id=55236,
    name='Outbreak',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=12, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=97,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of Plague Strike by $s1% and Scourge Strike by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskB_2': 134217728, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 1166, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50},
)


outbreak_55237 = spell(
    id=55237,
    name='Outbreak',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=97,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 55, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of Plague Strike by $s1% and Scourge Strike by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskB_2': 134217728, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RuneCostID': 1167, 'SpellClassSet': 15, 'SpellLevel': 55, 'SpellPriority': 50},
)


improved_icy_talons_55610 = _frost_rank(
    55610, 'Improved Icy Talons', rank=3, row=2, icon=101,
    school=School.FROST, attributes=80,
    effects=[
        Effect(type=65, base_points=9, implicit_target_a=_TARGET_SELF, apply_aura=AuraType.MOD_MELEE_HASTE,
               radius_yards=40.0),
    ],
    extra_raw={'AttributesEx7': 268435456, 'NameSubtext_Lang_enUS': ''},
    aura_description='Melee attack speed increased.',
    description=(
        'Increases the melee attack speed of all party and raid members within $a1 yards by $s1%.'
    ),
    notes=(
        'death-knight-rework S2 (user ruling 2026-10-25): no longer a talent (2223 is retired). The hidden party aura '
        'that is now the capstone of Icy Talons rank 3 (50885): a type-2 spell_linked_spell row on 50885 adds it with '
        'the rank and removes it with the rank (the Improved Icy Touch ranks / Vendetta ranks precedent). The one '
        'effect is the party area aura 138 MOD_MELEE_HASTE +10% (stored 9), radius 40 yd, always on; it also reaches '
        'the Death Knight (area auras include the owner, SpellAuras.cpp:2866). The former self effect (eff1, aura 193 '
        'HASTE_ALL +5%) is deleted: nothing reads it. Icon 101; the id, the name and the spell_group 1022 membership '
        'stay (group 1022 through the live nesting (1022, -1020) + (1020, 55610), rule 3 EXCLUSIVE_SAME_EFFECT, so '
        'the party aura does not stack with Air Attunement). Rank-3 SpellLevel (22), blank rank subtext. The stock '
        'RuneCostID / power type, the E0 / E1 class masks and the E2 twins are deleted.'
    ),
)


night_of_the_dead_55620 = spell(
    id=55620,
    name='Night of the Dead',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-45001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=-120001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=2718,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown on Raise Dead by ${$m1/-1000} sec and the cooldown on Army of the Dead by ${$m2/-60000} min.  Also reduces the damage your pet takes from creature area of effect attacks by $s3%.', 'EffectBasePoints_3': 44, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskB_1': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


night_of_the_dead_55623 = spell(
    id=55623,
    name='Night of the Dead',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-90001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=-240001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=2718,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown on Raise Dead by ${$m1/-1000} sec and the cooldown on Army of the Dead by ${$m2/-60000} min.  Also reduces the damage your pet takes from creature area of effect attacks by $s3%.', 'EffectBasePoints_3': 89, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EffectSpellClassMaskA_1': 4096, 'EffectSpellClassMaskB_1': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


desecration_55666 = spell(
    id=55666,
    name='Desecration',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=55741),
    ],
    spell_icon_id=2296,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31756, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Plague Strikes and Scourge Strikes cause the Desecrated Ground effect.  Targets in the area are slowed by $55741s1% by the grasping arms of the dead while standing on the unholy ground.  Lasts $55741d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassMask_1': 128, 'SpellClassSet': 15, 'SpellPriority': 50, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


desecration_55667 = spell(
    id=55667,
    name='Desecration',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=68766),
    ],
    spell_icon_id=2296,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'ChannelInterruptFlags': 31756, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Plague Strikes and Scourge Strikes cause the Desecrated Ground effect.  Targets in the area are slowed by $68766s1% by the grasping arms of the dead while standing on the unholy ground.  Lasts $68766d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassMask_1': 128, 'SpellClassSet': 15, 'SpellPriority': 50, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


rime_56822 = _frost_rank(
    56822, 'Rime', rank=2, row=3, icon=56,
    proc_chance=24, proc_type_mask=69904, attributes_ex3=_ATTR3_CAN_PROC_FROM_PROCS,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=_TARGET_SELF, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=59052),
    ],
    description=(
        'Your Obliterates have a $h% chance to make your next Howling Blast cost no runes and reset its '
        'cooldown.\n\n|cFF9D9D9DCapstone: Avalanche. Howling Blasts empowered by Rime also call down icicles on up '
        'to 5 enemies they hit, each dealing '
        + _AVALANCHE_POT +
        ' Frost damage.|r'
    ),
    notes=(
        'death-knight-rework S2a (Frost doc "Rime", D7 / U7): talent row 3, rank 2. ProcChance 24 (DBC; the '
        'spell_proc row -49188 has Chance 0 and inherits it, phase HIT stays). eff0 is a DUMMY: 0 on ranks 1 / 2, '
        '1 on rank 3 = the Avalanche capstone flag (the C++ gates on HasAura(59057), L4). eff1 stays '
        'PROC_TRIGGER_SPELL 59052 on EFFECT_1: spell_dk_rime registers on EFFECT_1 and resets Howling Blast\'s '
        'cooldown, moving it would lose the reset silently. The crit SpellMod (stock eff0) and its class mask are '
        'gone. ProcTypeMask 69904, AttributesEx3 and the two scripts on -49188 are kept. The capstone text quotes '
        'Avalanche 203321\'s potency through pot_text().'
    ),
)


reaping_56834 = spell(
    id=56834,
    name='Reaping',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=226, amplitude=30000),
    ],
    spell_icon_id=22,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever you hit with Blood Strike or Pestilence there is a $h% chance that the Blood Rune becomes a Death Rune when it activates.  Death Runes count as a Blood, Frost or Unholy Rune.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 66, 'ProcTypeMask': 69648, 'RangeIndex': 1, 'SpellClassSet': 15},
)


reaping_56835 = spell(
    id=56835,
    name='Reaping',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=226, amplitude=30000),
    ],
    spell_icon_id=22,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Whenever you hit with Blood Strike or Pestilence there is a $h% chance that the Blood Rune becomes a Death Rune when it activates.  Death Runes count as a Blood, Frost or Unholy Rune.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 69648, 'RangeIndex': 1, 'SpellClassSet': 15},
)


rime_59057 = _frost_rank(
    59057, 'Rime', rank=3, row=3, icon=56,
    proc_chance=35, proc_type_mask=69904, attributes_ex3=_ATTR3_CAN_PROC_FROM_PROCS,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=_TARGET_SELF, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=59052),
    ],
    description=(
        'Your Obliterates have a $h% chance to make your next Howling Blast cost no runes and reset its '
        'cooldown.\n\nCapstone: Avalanche. Howling Blasts empowered by Rime also call down icicles on up to 5 '
        'enemies they hit, each dealing '
        + _AVALANCHE_POT +
        ' Frost damage.'
    ),
    notes=(
        'death-knight-rework S2a (Frost doc "Rime", D7 / U7): talent row 3, rank 3. ProcChance 35 (DBC; the '
        'spell_proc row -49188 has Chance 0 and inherits it, phase HIT stays). eff0 is a DUMMY: 0 on ranks 1 / 2, '
        '1 on rank 3 = the Avalanche capstone flag (the C++ gates on HasAura(59057), L4). eff1 stays '
        'PROC_TRIGGER_SPELL 59052 on EFFECT_1: spell_dk_rime registers on EFFECT_1 and resets Howling Blast\'s '
        'cooldown, moving it would lose the reset silently. The crit SpellMod (stock eff0) and its class mask are '
        'gone. ProcTypeMask 69904, AttributesEx3 and the two scripts on -49188 are kept. The capstone text quotes '
        'Avalanche 203321\'s potency through pot_text().'
    ),
)


blood_gorged_61154 = spell(
    id=61154,
    name='Blood Gorged',
    school=School.NORMAL,
    attributes=400,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.LEARN_SPELL, base_points=1, implicit_target_a=1, trigger_spell=blood_gorged_50096.id),
        None,
        Effect(type=EffectType.LEARN_SPELL, base_points=1, implicit_target_a=1, trigger_spell=blood_gorged_61274.id),
    ],
    spell_icon_id=24,
    notes='S1a (Blood doc "Blood Gorged", brief D6): learn pair (50096, 61274) kept; damage 3%, armor penetration 3%. Rank 3 (61156) is the capstone, linked to the Mastery poll 203155 in deathknight_blood_b.py.',
    raw_overrides={'AttributesEx': 2147614720, 'AttributesEx4': 32768, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "While you are above 75% health, you deal 3% more damage. In addition, your attacks ignore 3% of your target's armor.\n\n|cFF9D9D9DCapstone: Your Mastery increases the damage bonus.|r", 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 20971521, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassSet': 15},
)


blood_gorged_61155 = spell(
    id=61155,
    name='Blood Gorged',
    school=School.NORMAL,
    attributes=400,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.LEARN_SPELL, base_points=3, implicit_target_a=1, trigger_spell=50108),
        None,
        Effect(type=EffectType.LEARN_SPELL, base_points=3, implicit_target_a=1, trigger_spell=61275),
    ],
    spell_icon_id=24,
    notes='S1a (Blood doc "Blood Gorged", brief D6): learn pair (50108, 61275) kept; damage 6%, armor penetration 6%. Rank 3 (61156) is the capstone, linked to the Mastery poll 203155 in deathknight_blood_b.py.',
    raw_overrides={'AttributesEx': 2147614720, 'AttributesEx4': 32768, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "While you are above 75% health, you deal 6% more damage. In addition, your attacks ignore 6% of your target's armor.\n\n|cFF9D9D9DCapstone: Your Mastery increases the damage bonus.|r", 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 20971521, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


blood_gorged_61156 = spell(
    id=61156,
    name='Blood Gorged',
    school=School.NORMAL,
    attributes=400,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.LEARN_SPELL, base_points=5, implicit_target_a=1, trigger_spell=50109),
        None,
        Effect(type=EffectType.LEARN_SPELL, base_points=5, implicit_target_a=1, trigger_spell=61276),
    ],
    spell_icon_id=24,
    notes='S1a (Blood doc "Blood Gorged", brief D6): learn pair (50109, 61276) kept; damage 9%, armor penetration 10%. Rank 3 (61156) is the capstone, linked to the Mastery poll 203155 in deathknight_blood_b.py.',
    raw_overrides={'AttributesEx': 2147614720, 'AttributesEx4': 32768, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "While you are above 75% health, you deal 9% more damage. In addition, your attacks ignore 10% of your target's armor.\n\nCapstone: Your Mastery increases the damage bonus.", 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 20971521, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


blood_gorged_61157 = spell(
    id=61157,
    name='Blood Gorged',
    school=School.NORMAL,
    attributes=400,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.LEARN_SPELL, base_points=7, implicit_target_a=1, trigger_spell=50110),
        None,
        Effect(type=EffectType.LEARN_SPELL, base_points=7, implicit_target_a=1, trigger_spell=61277),
    ],
    spell_icon_id=24,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 2147614720, 'AttributesEx4': 32768, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "When you are above 75% health, you deal $s1% more damage.  In addition, your attacks ignore up to $s3% of your opponent's armor at all times.", 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 20971521, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


blood_gorged_61158 = spell(
    id=61158,
    name='Blood Gorged',
    school=School.NORMAL,
    attributes=400,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.LEARN_SPELL, base_points=9, implicit_target_a=1, trigger_spell=50111),
        None,
        Effect(type=EffectType.LEARN_SPELL, base_points=9, implicit_target_a=1, trigger_spell=61278),
    ],
    spell_icon_id=24,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 2147614720, 'AttributesEx4': 32768, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "When you are above 75% health, you deal $s1% more damage.  In addition, your attacks ignore up to $s3% of your opponent's armor at all times.", 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 20971521, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15},
)


improved_death_strike_62905 = spell(
    id=62905,
    name='Improved Death Strike',
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
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=107, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=2751,
    notes='S1a (Blood doc "Improved Death Strike"): E1 damage +15 / 30% and E2 crit +3 / 6% on Death Strike (d0 b4) as before. E3 is now a typed ADD_PCT_MODIFIER SPELLMOD_DAMAGE +25 / +50% on the Death Strike heal 45470 (EffectSpellClassMaskC_3 = d2 b2 DEATH_STRIKE_HEAL); the stale raw E3 residue (EffectBasePoints_3 24 / 49, DieSides_3, ImplicitTargetA_3, the d0 0x10 mask C_1) is gone. NameSubtext fixed to Rank 2 on 62908.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712172, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Death Strike by 15%, its critical strike chance by 3%, and the healing it grants by 25%.\n\n|cFF9D9D9DCapstone: Healing from your Death Strike that exceeds your maximum health becomes a Blood Shield, absorbing damage of any school. Blood Shield stacks up to 30% of your maximum health and lasts 10 sec.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 16, 'EffectSpellClassMaskB_1': 16, 'EffectSpellClassMaskC_3': m.DEATH_STRIKE_HEAL, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


improved_death_strike_62908 = spell(
    id=62908,
    name='Improved Death Strike',
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
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=107, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=2751,
    notes='S1a (Blood doc "Improved Death Strike"): E1 damage +15 / 30% and E2 crit +3 / 6% on Death Strike (d0 b4) as before. E3 is now a typed ADD_PCT_MODIFIER SPELLMOD_DAMAGE +25 / +50% on the Death Strike heal 45470 (EffectSpellClassMaskC_3 = d2 b2 DEATH_STRIKE_HEAL); the stale raw E3 residue (EffectBasePoints_3 24 / 49, DieSides_3, ImplicitTargetA_3, the d0 0x10 mask C_1) is gone. NameSubtext fixed to Rank 2 on 62908.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712172, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Death Strike by 30%, its critical strike chance by 6%, and the healing it grants by 50%.\n\nCapstone: Healing from your Death Strike that exceeds your maximum health becomes a Blood Shield, absorbing damage of any school. Blood Shield stacks up to 30% of your maximum health and lasts 10 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 16, 'EffectSpellClassMaskB_1': 16, 'EffectSpellClassMaskC_3': m.DEATH_STRIKE_HEAL, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 15, 'SpellLevel': 1, 'SpellPriority': 50},
)


threat_of_thassarian_65661 = _frost_rank(
    65661, 'Threat of Thassarian', rank=1, row=7, icon=2023,
    equipped=(2, 41105),
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=_TARGET_SELF, apply_aura=AuraType.DUMMY),
    ],
    description=(
        'When dual-wielding, your Obliterate, Frost Strike, Heart Strike, Plague Strike and Death Strike have a '
        '$s1% chance to also deal damage with your off-hand weapon.'
    ),
    notes=(
        'death-knight-rework S2a (Frost doc "Threat of Thassarian", U16 / Q16): talent row 7, rank 1. eff0 DUMMY '
        'stored 32 = 33% (stock 30 / 60 / 100), read by spell_dk_threat_of_thassarian_rework. The spell_proc mask '
        '(m.TOT_PROC, HIT phase) and the rebind of -65661 are declared at the end of the file. EquippedItemClass 2 '
        '/ 41105 (stock weapon requirement) kept; the rank 3 filler DUMMY effect is kept as is.'
    ),
)


threat_of_thassarian_66191 = _frost_rank(
    66191, 'Threat of Thassarian', rank=2, row=7, icon=2023,
    equipped=(2, 41105),
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=65, implicit_target_a=_TARGET_SELF, apply_aura=AuraType.DUMMY),
    ],
    description=(
        'When dual-wielding, your Obliterate, Frost Strike, Heart Strike, Plague Strike and Death Strike have a '
        '$s1% chance to also deal damage with your off-hand weapon.'
    ),
    notes=(
        'death-knight-rework S2a (Frost doc "Threat of Thassarian", U16 / Q16): talent row 7, rank 2. eff0 DUMMY '
        'stored 65 = 66% (stock 30 / 60 / 100), read by spell_dk_threat_of_thassarian_rework. The spell_proc mask '
        '(m.TOT_PROC, HIT phase) and the rebind of -65661 are declared at the end of the file. EquippedItemClass 2 '
        '/ 41105 (stock weapon requirement) kept; the rank 3 filler DUMMY effect is kept as is.'
    ),
)


threat_of_thassarian_66192 = _frost_rank(
    66192, 'Threat of Thassarian', rank=3, row=7, icon=2023,
    equipped=(2, 41105),
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=_TARGET_SELF, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.DUMMY, die_sides=0),
    ],
    description=(
        'When dual-wielding, your Obliterate, Frost Strike, Heart Strike, Plague Strike and Death Strike have a '
        '$s1% chance to also deal damage with your off-hand weapon.'
    ),
    notes=(
        'death-knight-rework S2a (Frost doc "Threat of Thassarian", U16 / Q16): talent row 7, rank 3. eff0 DUMMY '
        'stored 99 = 100% (stock 30 / 60 / 100), read by spell_dk_threat_of_thassarian_rework. The spell_proc mask '
        '(m.TOT_PROC, HIT phase) and the rebind of -65661 are declared at the end of the file. EquippedItemClass 2 '
        '/ 41105 (stock weapon requirement) kept; the rank 3 filler DUMMY effect is kept as is.'
    ),
)


desolation_66799 = spell(
    id=66799,
    name='Desolation',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=63583),
    ],
    spell_icon_id=95,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Blood Strikes cause you to deal $63583s1% additional damage with all attacks for the next $63583d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassMask_1': 128, 'SpellClassSet': 15, 'SpellPriority': 50, 'StartRecoveryCategory': 133},
)


desolation_66814 = spell(
    id=66814,
    name='Desolation',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=66800),
    ],
    spell_icon_id=95,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Blood Strikes cause you to deal $66800s1% additional damage with all attacks for the next $66800d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassMask_1': 128, 'SpellClassSet': 15, 'SpellPriority': 50, 'StartRecoveryCategory': 133},
)


desolation_66815 = spell(
    id=66815,
    name='Desolation',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=66801),
    ],
    spell_icon_id=95,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Blood Strikes cause you to deal $66801s1% additional damage with all attacks for the next $66801d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassMask_1': 128, 'SpellClassSet': 15, 'SpellPriority': 50, 'StartRecoveryCategory': 133},
)


desolation_66816 = spell(
    id=66816,
    name='Desolation',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=66802),
    ],
    spell_icon_id=95,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Blood Strikes cause you to deal $66802s1% additional damage with all attacks for the next $66802d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassMask_1': 128, 'SpellClassSet': 15, 'SpellPriority': 50, 'StartRecoveryCategory': 133},
)


desolation_66817 = spell(
    id=66817,
    name='Desolation',
    school=School.SHADOW,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=66803),
    ],
    spell_icon_id=95,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Blood Strikes cause you to deal $66803s1% additional damage with all attacks for the next $66803d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 16, 'RangeIndex': 1, 'SpellClassMask_1': 128, 'SpellClassSet': 15, 'SpellPriority': 50, 'StartRecoveryCategory': 133},
)


# ---------------------------------------------------------------------------
# Potency system P8 (pets, guardians, totems): Ebon Gargoyle's own attack,
# npc_pet_dk_ebon_gargoyle (ScriptedAI, pet_dk.cpp) via plain DoCastVictim -
# caster = the gargoyle, which Summon Gargoyle (49206/50514, SPELL_EFFECT_SUMMON)
# spawns at exactly the owner's level through Spell::SummonGuardian's default
# summonLevel = caster->GetLevel() (no per-spell exception for this summon id).
#
# Wrinkle: spell_pet_dk_gargoyle_strike (SpellScript, same file) reads
# GetEffectValue() in OnEffectLaunchTarget - i.e. AFTER CalcValue()/this hook
# has already run - and adds a flat (casterLevel-60)*3 on top via
# SetEffectValue(), only when the caster is level >= 60. This is purely
# additive on whatever CalcValue() produces (not a base-point override), so it
# composes cleanly with potency and needs zero script changes - just a note
# that the live post-conversion number above level 60 will read a bit higher
# than the raw potency value below implies.
# ---------------------------------------------------------------------------
gargoyle_strike_51963 = spell(
    id=51963,
    name='Gargoyle Strike',
    school=School.NATURE,
    attributes=589824,
    cast_time_ms=2000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=16.8, potency_kind='direct', implicit_target_a=6),
    ],
    spell_icon_id=213,
    notes="pulled from existing data. Potency system P8: Ebon Gargoyle's own attack (DoCastVictim, "
          "no custom bp). Base-implied sp_potency=16.8 from the flat (no RealPointsPerLevel) V60 "
          "average of 60 (50 base + die_sides=19 mean 10); the live EffectBonusMultiplier_1 (0.453) "
          "implies a far higher 79.3 - base wins by default (docs/potency-system.md). The '0.453' "
          "coefficient lives in the SP (direct_bonus) column, not AP, even though the spell's own "
          "flavor text says 'modified by attack power' - Pet.cpp's NPC_EBON_GARGOYLE case adds "
          "SPELL_DK_PET_SCALING_01/02/03 auras that convert the owner's attack power into the "
          "gargoyle's own effective spell power stat, so Unit::SpellDamageBonusDone's SP path is "
          "what the engine actually reads for this creature; ap_potency/ap_bonus would instead read "
          "the AP path, which this pet's damage formula never uses, silently zeroing its scaling. "
          "Kept as sp_potency to match the live mechanism exactly (docs/potency-system.md's pets "
          "section: 'the stock inheritance of owner spell power and attack power stays as is').",
    raw_overrides={'FacingCasterFlags': 1, 'CastingTimeIndex': 5, 'InterruptFlags': 15, 'ProcChance': 101, 'BaseLevel': 55, 'SpellLevel': 55, 'DurationIndex': 0, 'Speed': 20.0, 'EquippedItemClass': -1, 'SpellVisualID_1': 4379, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Inflicts Nature damage to an enemy.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)
unbind_bonus_coefficients(gargoyle_strike_51963)  # stale spell_bonus_data row overrode the potency coefficient (D1)

# Frost Fever's disease damage is exempt from the binary-spell roll (T0 headline 3; SPELL_ATTR0_CU_IGNORE_BINARY). 55095 itself
# is declared in source/spells/npc.csv (not a DSL spell here), so this row replaces nothing and duplicates nothing.
custom_attr(55095, 0x200)

# ---- S1a pulls (Scent of Blood, Veteran of the Third War, Bloody Vengeance ranks; pulled from stock, edited by A2) ----
scent_of_blood_49004 = spell(
    id=49004,
    name='Scent of Blood',
    school=1,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=6, implicit_target_a=1, apply_aura=42, trigger_spell=50421),
    ],
    spell_icon_id=2283,
    notes='S1a (Blood doc "Scent of Blood", brief D4): ONE PROC_TRIGGER_SPELL -> 50421 effect per rank (the stock ranks 2 / 3 carried 2 / 3 effects = 2 / 3 stacks per proc). ProcChance 5 / 10 / 15 on the rank spell, spell_proc -49004 Chance 0 = use the spell\'s, Cooldown 10000, HitMask 0x33 kept (declared at the end of this file). ProcTypeMask 0x222A8 kept (taken hits, no periodic). The buff 50421 (3 charges, 20 s, reset on re-proc) is in deathknight_blood_helpers.py.',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You have a 5% chance after dodging, parrying or taking direct damage to gain Scent of Blood, causing your next 3 melee hits to generate 10 Runic Power. This effect cannot occur more than once every 10 sec.', 'DurationIndex': 0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 5, 'ProcTypeMask': 139944, 'RangeIndex': 1, 'SpellLevel': 1, 'SpellPriority': 50},
)


scent_of_blood_49508 = spell(
    id=49508,
    name='Scent of Blood',
    school=1,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=6, implicit_target_a=1, apply_aura=42, trigger_spell=50421),
    ],
    spell_icon_id=2283,
    notes='S1a (Blood doc "Scent of Blood", brief D4): ONE PROC_TRIGGER_SPELL -> 50421 effect per rank (the stock ranks 2 / 3 carried 2 / 3 effects = 2 / 3 stacks per proc). ProcChance 5 / 10 / 15 on the rank spell, spell_proc -49004 Chance 0 = use the spell\'s, Cooldown 10000, HitMask 0x33 kept (declared at the end of this file). ProcTypeMask 0x222A8 kept (taken hits, no periodic). The buff 50421 (3 charges, 20 s, reset on re-proc) is in deathknight_blood_helpers.py.',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You have a 10% chance after dodging, parrying or taking direct damage to gain Scent of Blood, causing your next 3 melee hits to generate 10 Runic Power. This effect cannot occur more than once every 10 sec.', 'DurationIndex': 0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 10, 'ProcTypeMask': 139944, 'RangeIndex': 1, 'SpellLevel': 1, 'SpellPriority': 50},
)


scent_of_blood_49509 = spell(
    id=49509,
    name='Scent of Blood',
    school=1,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=6, implicit_target_a=1, apply_aura=42, trigger_spell=50421),
    ],
    spell_icon_id=2283,
    notes='S1a (Blood doc "Scent of Blood", brief D4): ONE PROC_TRIGGER_SPELL -> 50421 effect per rank (the stock ranks 2 / 3 carried 2 / 3 effects = 2 / 3 stacks per proc). ProcChance 5 / 10 / 15 on the rank spell, spell_proc -49004 Chance 0 = use the spell\'s, Cooldown 10000, HitMask 0x33 kept (declared at the end of this file). ProcTypeMask 0x222A8 kept (taken hits, no periodic). The buff 50421 (3 charges, 20 s, reset on re-proc) is in deathknight_blood_helpers.py.',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You have a 15% chance after dodging, parrying or taking direct damage to gain Scent of Blood, causing your next 3 melee hits to generate 10 Runic Power. This effect cannot occur more than once every 10 sec.', 'DurationIndex': 0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 15, 'ProcTypeMask': 139944, 'RangeIndex': 1, 'SpellLevel': 1, 'SpellPriority': 50},
)


veteran_of_the_third_war_49006 = spell(
    id=49006,
    name='Veteran of the Third War',
    school=1,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=137),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=137, misc_value=2),
    ],
    spell_icon_id=2615,
    notes='S1a (Blood doc "Veteran of the Third War"): E3 (aura 240, expertise) dropped, Expertise is removed from the server. E1 Strength bp 1 / 3 / 5, E2 Stamina bp 0 / 1 / 2 unchanged.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Strength by 2% and your Stamina by 1%.', 'DurationIndex': 0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellLevel': 1, 'SpellPriority': 50},
)


veteran_of_the_third_war_49526 = spell(
    id=49526,
    name='Veteran of the Third War',
    school=1,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=137),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=137, misc_value=2),
    ],
    spell_icon_id=2615,
    notes='S1a (Blood doc "Veteran of the Third War"): E3 (aura 240, expertise) dropped, Expertise is removed from the server. E1 Strength bp 1 / 3 / 5, E2 Stamina bp 0 / 1 / 2 unchanged.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Strength by 4% and your Stamina by 2%.', 'DurationIndex': 0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellLevel': 1, 'SpellPriority': 50},
)


veteran_of_the_third_war_50029 = spell(
    id=50029,
    name='Veteran of the Third War',
    school=1,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=137),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=137, misc_value=2),
    ],
    spell_icon_id=2615,
    notes='S1a (Blood doc "Veteran of the Third War"): E3 (aura 240, expertise) dropped, Expertise is removed from the server. E1 Strength bp 1 / 3 / 5, E2 Stamina bp 0 / 1 / 2 unchanged.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Strength by 6% and your Stamina by 3%.', 'DurationIndex': 0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellLevel': 1, 'SpellPriority': 50},
)


bloody_vengeance_48988 = spell(
    id=48988,
    name='Bloody Vengeance',
    school=1,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=6, die_sides=0, implicit_target_a=1, apply_aura=42, trigger_spell=50447),
    ],
    spell_icon_id=243,
    notes='S1a (Blood doc "Bloody Vengeance", brief D1): ProcTypeMask 0x11154 + DONE_PERIODIC 0x40000 = 0x51154 (any crit by the DK, including periodic crits). spell_proc -48988 (end of this file): crit hit, phase HIT, PROC_ATTR_TRIGGERED_CAN_PROC. The buffs 50447-50449 (all damage, misc 127, 3 stacks, 30 s) are deathknight_blood_helpers.py\'s.',
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all damage you deal by 1% for 30 sec after you deal a critical strike from a weapon swing, spell or ability. Stacks up to 3 times.', 'DurationIndex': 0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 0x51154, 'RangeIndex': 1},
)


bloody_vengeance_49503 = spell(
    id=49503,
    name='Bloody Vengeance',
    school=1,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=6, die_sides=0, implicit_target_a=1, apply_aura=42, trigger_spell=50448),
    ],
    spell_icon_id=243,
    notes='S1a (Blood doc "Bloody Vengeance", brief D1): ProcTypeMask 0x11154 + DONE_PERIODIC 0x40000 = 0x51154 (any crit by the DK, including periodic crits). spell_proc -48988 (end of this file): crit hit, phase HIT, PROC_ATTR_TRIGGERED_CAN_PROC. The buffs 50447-50449 (all damage, misc 127, 3 stacks, 30 s) are deathknight_blood_helpers.py\'s.',
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all damage you deal by 2% for 30 sec after you deal a critical strike from a weapon swing, spell or ability. Stacks up to 3 times.', 'DurationIndex': 0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 0x51154, 'RangeIndex': 1},
)


bloody_vengeance_49504 = spell(
    id=49504,
    name='Bloody Vengeance',
    school=1,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=6, die_sides=0, implicit_target_a=1, apply_aura=42, trigger_spell=50449),
    ],
    spell_icon_id=243,
    notes='S1a (Blood doc "Bloody Vengeance", brief D1): ProcTypeMask 0x11154 + DONE_PERIODIC 0x40000 = 0x51154 (any crit by the DK, including periodic crits). spell_proc -48988 (end of this file): crit hit, phase HIT, PROC_ATTR_TRIGGERED_CAN_PROC. The buffs 50447-50449 (all damage, misc 127, 3 stacks, 30 s) are deathknight_blood_helpers.py\'s.',
    raw_overrides={'AttributesEx3': 67633152, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all damage you deal by 3% for 30 sec after you deal a critical strike from a weapon swing, spell or ability. Stacks up to 3 times.', 'DurationIndex': 0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 0x51154, 'RangeIndex': 1},
)


# ---- S1a (Blood): spell_proc rows and script bindings for the Blood talent ranks edited above --------------------------------------
# Every DONE spell-class / DONE_PERIODIC row carries spell_phase_mask 2 (HIT). A negative key is the stock "this spell and every rank
# of its talent chain" form (ObjectMgr / SpellMgr expand it); a row declared here replaces the stock spell_proc.sql row of that key.
_PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS = 0x10
_PROC_FLAGS_BLOODY_VENGEANCE = 0x51154       # DONE melee auto 0x4 | spell melee 0x10 | ranged auto 0x40 | spell ranged 0x100 | none-class neg 0x1000 | magic neg 0x10000 | periodic 0x40000
_PROC_SPELL_TYPE_DAMAGE = 0x1
_PROC_SPELL_PHASE_HIT = 0x2
_PROC_HIT_CRITICAL = 0x2
_PROC_HIT_SCENT_OF_BLOOD = 0x33              # NORMAL | CRITICAL | DODGE | PARRY (the stock row's value)
_PROC_ATTR_TRIGGERED_CAN_PROC = 0x2

# Subversion capstone (rank 3, effect 2 -> 203152 +5 Runic Power): a crit of Heart Strike / Marrowrend / Obliterate / Scourge Strike.
# Effect 1 (the crit SpellMod) never procs (DisableEffectsMask 0x1); once per cast is spell_dk_subversion_capstone (RuneProcAllowed).
procs_on(subversion_49491, proc_flags=_PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS, family_name=_SPELLFAMILY_DEATHKNIGHT,
         family_mask=m.SUBVERSION_READ, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=_PROC_SPELL_PHASE_HIT,
         hit_mask=_PROC_HIT_CRITICAL, chance=100.0, disable_effects_mask=0x1)
scripted_by(subversion_49491, 'spell_dk_subversion_capstone')

# Scent of Blood: the stock row (HitMask 0x33, Chance 0 = the rank spell's 5 / 10 / 15) plus the 10 s internal cooldown. The stock
# bindings on -49004 (spell_dk_scent_of_blood_trigger, spell_gen_proc_from_direct_damage) stay.
procs_on(-49004, proc_flags=0, hit_mask=_PROC_HIT_SCENT_OF_BLOOD, cooldown_ms=10000)

# Bloody Vengeance: any crit by the DK, periodic crits included; a triggered cast may proc it (D&D ticks, brief D1).
procs_on(-48988, proc_flags=_PROC_FLAGS_BLOODY_VENGEANCE, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_CRITICAL, attributes_mask=_PROC_ATTR_TRIGGERED_CAN_PROC)

# Bloodworms: the stock row without the 20 s internal cooldown (Blood doc Q10). The talent script is new.
procs_on(-49027, proc_flags=0, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=_PROC_SPELL_PHASE_HIT, cooldown_ms=0)
scripted_by(-49027, 'spell_dk_bloodworms_talent')

# Sudden Doom: Heart Strike + Blood Boil (was d0 0x1400000, Heart Strike + Blood Strike). The stock script spell_dk_sudden_doom keeps
# casting the Death Coil; the second script gates the proc to once per cast.
procs_on(-49018, proc_flags=0, family_name=_SPELLFAMILY_DEATHKNIGHT, family_mask=m.SUDDEN_DOOM_PROC,
         spell_type_mask=_PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=_PROC_SPELL_PHASE_HIT)
scripted_by(-49018, 'spell_dk_sudden_doom_once')


# ---- S2a: pulled stock rank spells (Toughness r1-r3, Nerves of Cold Steel r1-r3), edited in place by the Frost tree ----
toughness_49042 = _frost_rank(
    49042, 'Toughness', rank=1, row=0, icon=52,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=_TARGET_SELF, apply_aura=AuraType.MOD_CUSTOM_STAT_PCT,
               misc_value=_CR_VERSATILITY),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.MOD_BASE_RESISTANCE_PCT, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=_TARGET_SELF, apply_aura=232,
               misc_value=11),
    ],
    description=(
        'Increases your Versatility by $s1% and your armor value from items by $s2%, and reduces the duration of '
        'all movement slowing effects on you by $s3%.'
    ),
    notes=(
        'death-knight-rework S2a (Frost doc "Toughness", S2-HANDOFF U23): talent row 0, 3 ranks (the stock ranks 4 '
        '/ 5, 49788 / 49789, are not declared). eff0 aura 306 MOD_CUSTOM_STAT_PCT misc 1 << 21 (Versatility) +1 / '
        '2 / 3%, eff1 aura 142 item armor +3 / 6 / 10%, eff2 aura 232 MECHANIC_DURATION_MOD misc 11 (slow) -10 / '
        '20 / 30%. Stored = value - 1. Pulled from the stock row in WP-0.2.'
    ),
)


toughness_49786 = _frost_rank(
    49786, 'Toughness', rank=2, row=0, icon=52,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.MOD_CUSTOM_STAT_PCT, misc_value=_CR_VERSATILITY),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.MOD_BASE_RESISTANCE_PCT, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=_TARGET_SELF, apply_aura=232,
               misc_value=11),
    ],
    description=(
        'Increases your Versatility by $s1% and your armor value from items by $s2%, and reduces the duration of '
        'all movement slowing effects on you by $s3%.'
    ),
    notes=(
        'death-knight-rework S2a (Frost doc "Toughness", S2-HANDOFF U23): talent row 0, 3 ranks (the stock ranks 4 '
        '/ 5, 49788 / 49789, are not declared). eff0 aura 306 MOD_CUSTOM_STAT_PCT misc 1 << 21 (Versatility) +1 / '
        '2 / 3%, eff1 aura 142 item armor +3 / 6 / 10%, eff2 aura 232 MECHANIC_DURATION_MOD misc 11 (slow) -10 / '
        '20 / 30%. Stored = value - 1. Pulled from the stock row in WP-0.2.'
    ),
)


toughness_49787 = _frost_rank(
    49787, 'Toughness', rank=3, row=0, icon=52,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.MOD_CUSTOM_STAT_PCT, misc_value=_CR_VERSATILITY),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=_TARGET_SELF,
               apply_aura=AuraType.MOD_BASE_RESISTANCE_PCT, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=_TARGET_SELF, apply_aura=232,
               misc_value=11),
    ],
    description=(
        'Increases your Versatility by $s1% and your armor value from items by $s2%, and reduces the duration of '
        'all movement slowing effects on you by $s3%.'
    ),
    notes=(
        'death-knight-rework S2a (Frost doc "Toughness", S2-HANDOFF U23): talent row 0, 3 ranks (the stock ranks 4 '
        '/ 5, 49788 / 49789, are not declared). eff0 aura 306 MOD_CUSTOM_STAT_PCT misc 1 << 21 (Versatility) +1 / '
        '2 / 3%, eff1 aura 142 item armor +3 / 6 / 10%, eff2 aura 232 MECHANIC_DURATION_MOD misc 11 (slow) -10 / '
        '20 / 30%. Stored = value - 1. Pulled from the stock row in WP-0.2.'
    ),
)


nerves_of_cold_steel_49226 = _frost_rank(
    49226, 'Nerves of Cold Steel', rank=1, row=6, icon=533,
    equipped=(2, 41105),
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=_TARGET_SELF, apply_aura=122),
    ],
    description='Increases the damage done by your off-hand weapon by $s1%.',
    notes=(
        'death-knight-rework S2a (Frost doc "Nerves of Cold Steel", U23): talent row 6, rank 1. aura 122 '
        'MOD_OFFHAND_DAMAGE_PCT 8% (stock value) in eff0; the stock eff0 aura 54 (hit chance, hit no longer '
        'exists) is dropped. EquippedItemClass 2 / 41105 (the stock weapon requirement) kept. Pulled from the '
        'stock row in WP-0.2.'
    ),
)


nerves_of_cold_steel_50137 = _frost_rank(
    50137, 'Nerves of Cold Steel', rank=2, row=6, icon=533,
    equipped=(2, 41105),
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=_TARGET_SELF, apply_aura=122),
    ],
    description='Increases the damage done by your off-hand weapon by $s1%.',
    notes=(
        'death-knight-rework S2a (Frost doc "Nerves of Cold Steel", U23): talent row 6, rank 2. aura 122 '
        'MOD_OFFHAND_DAMAGE_PCT 16% (stock value) in eff0; the stock eff0 aura 54 (hit chance, hit no longer '
        'exists) is dropped. EquippedItemClass 2 / 41105 (the stock weapon requirement) kept. Pulled from the '
        'stock row in WP-0.2.'
    ),
)


nerves_of_cold_steel_50138 = _frost_rank(
    50138, 'Nerves of Cold Steel', rank=3, row=6, icon=533,
    equipped=(2, 41105),
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=_TARGET_SELF, apply_aura=122),
    ],
    description='Increases the damage done by your off-hand weapon by $s1%.',
    notes=(
        'death-knight-rework S2a (Frost doc "Nerves of Cold Steel", U23): talent row 6, rank 3. aura 122 '
        'MOD_OFFHAND_DAMAGE_PCT 25% (stock value) in eff0; the stock eff0 aura 54 (hit chance, hit no longer '
        'exists) is dropped. EquippedItemClass 2 / 41105 (the stock weapon requirement) kept. Pulled from the '
        'stock row in WP-0.2.'
    ),
)


# ---- S2a (Frost): spell_proc rows, script bindings and link rows for the Frost talent ranks edited above ---------------------------
# A negative key is the stock "this spell and every rank of its chain" form; a row declared under a key replaces the live row of that key.
_PROC_FLAG_DONE_MELEE_AUTO_ATTACK = 0x4
_PROC_SPELL_PHASE_CAST = 0x1
_PROC_HIT_THREAT_OF_THASSARIAN = 0x477       # NORMAL | CRITICAL | MISS | DODGE | PARRY | BLOCK | ABSORB (the stock row's value)

# Killing Machine (D8 / U6): per-rank POSITIVE rows (the live ones were PPM 1 / 2 / 3 per rank; declaring -51123 while the positive
# rows are live would shadow them, lint check_shadowed_spell_procs). DONE_MELEE_AUTO_ATTACK covers both hands; the Chance is the
# two-hander value, spell_dk_killing_machine_talent (CheckProc: owner, not triggered, one-hander) halves it. The auto attack flag
# carries no spell phase, so SpellPhaseMask stays 0 (a phase on a non-spell flag logs "won't be used" at boot and fails the lint).
# Ranks 4 / 5 (51129 / 51130) are no longer granted: their stock PPM rows go.
procs_on(killing_machine_51123, proc_flags=_PROC_FLAG_DONE_MELEE_AUTO_ATTACK, chance=6.0)
procs_on(killing_machine_51127, proc_flags=_PROC_FLAG_DONE_MELEE_AUTO_ATTACK, chance=12.0)
procs_on(killing_machine_51128, proc_flags=_PROC_FLAG_DONE_MELEE_AUTO_ATTACK, chance=20.0)
remove_spell_proc(51129)
remove_spell_proc(51130)
unbind_script(-51123, 'spell_gen_no_offhand_proc')       # it blocks off-hand procs (spell_generic.cpp:815-829); off-hand swings roll too
scripted_by(-51123, 'spell_dk_killing_machine_talent')

# Chill of the Grave (U19): a CAST-phase proc on Obliterate + Howling Blast (fires once per non-triggered cast, null victim; the
# energize 50480 targets the caster). The live row was Icy Touch + Chains of Ice + Howling Blast + Obliterate on the HIT phase.
procs_on(-49149, proc_flags=0, family_name=_SPELLFAMILY_DEATHKNIGHT, family_mask=m.CHILL_OF_THE_GRAVE_PROC,
         spell_phase_mask=_PROC_SPELL_PHASE_CAST)

# Threat of Thassarian (U16): the stock roll_chance_i script lacks Proc Chance and maps Blood Strike / Rune Strike; the rework roll
# is roll_chance_f(amount x (1 + ProcChance%)), OncePerCastGuard (Heart Strike cleaves). Mask = Heart Strike + Plague Strike + Death
# Strike (d0) and Frost Strike + Obliterate (d1), HIT phase; every other field is the live row's.
procs_on(-65661, proc_flags=_PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS, family_name=_SPELLFAMILY_DEATHKNIGHT,
         family_mask=m.TOT_PROC, spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_THREAT_OF_THASSARIAN, chance=100.0)
unbind_script(-65661, 'spell_dk_threat_of_thassarian')
scripted_by(-65661, 'spell_dk_threat_of_thassarian_rework')

# Blood of the North (D9): eff0 is now a plain SpellMod, so the Death Rune conversion row goes. The ProcTypeMask of the three ranks
# is 0 (above), otherwise the DBC flags (87312) would rebuild a default row. spell_dk_death_rune stays bound to -49208 / -49467.
remove_spell_proc(-54639)
unbind_script(-54639, 'spell_dk_death_rune')

# Improved Icy Touch (U15 / U23): each rank links its helper (203323-203325, deathknight_frost_b.py: SPELLMOD_DOT +5 / 10 / 15 on
# Frost Fever, rank 3 also SPELLMOD_RANGE +10 yd on Icy Touch / Chains of Ice / Howling Blast), type 2 = applied and removed with the aura.
linked_spell(49175, 203323, 2, comment='Improved Icy Touch rank 1 - Frost Fever damage helper (S2a)')
linked_spell(50031, 203324, 2, comment='Improved Icy Touch rank 2 - Frost Fever damage helper (S2a)')
linked_spell(51456, 203325, 2, comment='Improved Icy Touch rank 3 - Frost Fever damage + range helper (S2a)')

# Icy Talons capstone (user ruling 2026-10-25): rank 3 links the hidden party/raid melee haste aura 55610 (ex Improved Icy Talons),
# type 2 = applied and removed with the aura (SpellAuras.cpp), the same shape as Improved Icy Touch above.
linked_spell(50885, improved_icy_talons_55610.id, 2, comment='Icy Talons rank 3 - party/raid melee haste capstone (S2)')

# Strike script bindings (S2a-HANDOFF "Script classes"). 66216 and 203322 are bound in deathknight_frost_helpers.py / _frost_b.py.
scripted_by(icy_touch_45477, 'spell_dk_icy_touch_rework')
scripted_by(heart_strike_55050, 'spell_dk_heart_strike_frost')
scripted_by(plague_strike_45462, 'spell_dk_plague_strike_frost')
scripted_by(obliterate_66198, 'spell_dk_frost_offhand')
scripted_by(frost_strike_66196, 'spell_dk_frost_offhand')
