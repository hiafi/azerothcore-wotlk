"""
Paladin - player-castable spells (real cast_time_ms/cooldown_ms, not marked passive).

Split from a single source/classes/paladin.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .paladin_...` below) resolve.
"""

from lib.dsl import RANGE_SELF, AuraType, DispelType, Effect, EffectType, Mechanic, School
from lib.dsl.registry import (
    linked_spell,
    pot_text,
    procs_on,
    scripted_by,
    skill_line_ability,
    spell,
    spell_category,
    trained_by,
    unbind_script,
    unrank_spells,
    unrequire_spell,
    untrain,
)

from . import _masks as m
from .paladin_holy_spells import holy_heal_tooltip
from .paladin_prot_spells import prot_holy_shield_tooltip, prot_sor_tooltip
from .paladin_trigger_spells import holy_shock_25912, holy_shock_25914, sacred_shield_58597


# paladin-rework S1 (SHARED C2.1 / C2.2a): -30% damage taken, 2 min cooldown, no Forbearance cause/check
# (spell_pal_immunities unbound below), ExcludeCasterAuraSpell 61988 dropped (nothing applies 61988 for Divine Protection).
divine_protection_498 = spell(
    id=498,
    name='Divine Protection',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    mechanic=29,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=0.0,
    duration_ms=12000,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
    ],
    spell_icon_id=73,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 2097152, 'AttributesEx5': 4, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage taken reduced by $s2%.', 'AuraInterruptFlags': 4718592, 'BaseLevel': 6, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces all damage taken by $s2% for $d.', 'EffectBasePoints_1': -101, 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_1': 1, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 4194304, 'SpellClassMask_3': 256, 'SpellClassSet': 10, 'SpellLevel': 6, 'SpellVisualID_1': 11817},
)


# paladin-rework S1 (SHARED C2.1 / C2.2b): 5 min cooldown, no Forbearance / Avenging Wrath lockout text.
lay_on_hands_633 = spell(
    id=633,
    name='Lay on Hands',
    school=School.HOLY,
    attributes=327680,
    category=56,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=300000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=40.0,
    effects=[
        Effect(type=67, base_points=-1, implicit_target_a=21),
        Effect(type=EffectType.ENERGIZE, base_points=249, implicit_target_a=21),
    ],
    spell_icon_id=79,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 10, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Heals a friendly target for an amount equal to the Paladin's maximum health.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 32768, 'SpellClassSet': 10, 'SpellLevel': 10, 'SpellVisualID_1': 132, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


holy_light_635 = spell(
    id=635,
    name='Holy Light',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=2500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=29,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, sp_potency=135.0, potency_kind='heal', implicit_target_a=21),
    ],
    spell_icon_id=70,
    tooltip_vars=holy_heal_tooltip,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 13 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. Potency system P7 (paladin pass): converted to sp_potency=135.0 (paladin-potency-proposals.txt, user value; was 207.8 from a stale worktree copy of the proposals file, corrected 2026-10-02). | paladin-rework S2 HOLY 4.1: sp_potency 150 -> 135 (2,383 at 60); description {pot1} -> {pot1*hl} (entry 1105 owned by paladin_holy_spells.py).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 20, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals a friendly target for {pot1*hl}.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 10, 'SpellLevel': 1, 'SpellVisualID_1': 2936, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


hammer_of_justice_853 = spell(
    id=853,
    name='Hammer of Justice',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    mechanic=Mechanic.STUN,
    attributes=327680,
    category=32,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=60000,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=10.0,
    duration_ms=3000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
    ],
    spell_icon_id=302,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 8); RealPointsPerLevel from rank1->covers-60 (anchor rank 4 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 262144, 'AttributesEx6': 8388608, 'AttributesEx7': 2048, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Stunned.', 'AuraInterruptFlags': 4718592, 'BaseLevel': 8, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Stuns the target for $d and interrupts non-player spellcasting for $32747d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 2048, 'SpellClassSet': 10, 'SpellLevel': 8, 'SpellVisualID_1': 322, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


# paladin-rework S1 (SHARED B5.8 / B9): 125 / 125 potency; tooltip multiplies by tooltip_vars 1104 `mult_exo` (declared in paladin_seal_spells.py).
exorcism_879 = spell(
    id=879,
    name='Exorcism',
    school=School.HOLY,
    attributes=327680,
    category=19,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=15000,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=125.0, ap_potency=125.0, potency_kind='direct', implicit_target_a=6),
    ],
    spell_icon_id=292,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. Potency system P7 (paladin pass): converted to sp_potency=140.0 / ap_potency=140.0 (paladin-potency-proposals.txt total 280.0, user value; was 271.8 from a stale worktree copy, corrected 2026-10-02; split evenly - matches the pre-existing 0.15/0.15 equal SP/AP coefficient split); also fixes PLAN F13 (the single-rank migration had zeroed this spell\'s spell_bonus_data direct_bonus, killing its live SP scaling - this conversion restores it as a side effect, same as docs/potency-system.md\'s "Known live bug" note).',
    raw_overrides={'AttributesEx': 512, 'AttributesEx6': 33554432, 'AttributesEx7': 32768, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes {pot1*mult_exo} Holy damage to an enemy target.  If the target is Undead or Demon, it will always critically hit.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 2, 'SpellClassSet': 10, 'SpellDescriptionVariableID': 1104, 'SpellLevel': 20, 'SpellVisualID_1': 324, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


# paladin-rework S1 (SHARED B5.5 / C2.1): tooltip drops Divine Protection (no longer causes Forbearance) and the Avenging Wrath sentence.
hand_of_protection_1022 = spell(
    id=1022,
    name='Hand of Protection',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    mechanic=29,
    attributes=327680,
    category=20,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=300000,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=30.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=57, apply_aura=39, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=57, apply_aura=AuraType.MOD_PACIFY),
    ],
    spell_icon_id=303,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 32768, 'AttributesEx2': 2097152, 'AttributesEx5': 4, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Immune to physical attacks.  Cannot attack or use physical abilities.', 'AuraInterruptFlags': 4718592, 'BaseLevel': 10, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'A targeted party or raid member is protected from all physical attacks for $d, but during that time they cannot attack or use physical abilities.  Players may only have one Hand on them per Paladin at any one time.  Once protected, the target cannot be targeted by Divine Shield or Hand of Protection again for $25771d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ExcludeTargetAuraSpell': 61988, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 128, 'SpellClassSet': 10, 'SpellLevel': 10, 'SpellVisualID_1': 302, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


hand_of_salvation_1038 = spell(
    id=1038,
    name='Hand of Salvation',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=329728,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=30.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=57, apply_aura=227, amplitude=1000, misc_value=127, trigger_spell=53055),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=57, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
    ],
    spell_icon_id=305,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Reduces total threat by $53055s1% each second.', 'BaseLevel': 26, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Places a Hand on the party or raid member, reducing their total threat by $53055s1% every $t1 sec. for $d.  Players may only have one Hand on them per Paladin at any one time.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 256, 'SpellClassSet': 10, 'SpellLevel': 26, 'SpellVisualID_1': 300, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


hand_of_freedom_1044 = spell(
    id=1044,
    name='Hand of Freedom',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=25000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=30.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=21, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=21, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=11),
    ],
    spell_icon_id=80,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 163840, 'AttributesEx5': 8, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Immune to movement impairing effects.', 'BaseLevel': 18, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Places a Hand on the friendly target, granting immunity to movement impairing effects for $d.  Players may only have one Hand on them per Paladin at any one time.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 16, 'SpellClassSet': 10, 'SpellLevel': 18, 'SpellVisualID_1': 4050, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


purify_1152 = spell(
    id=1152,
    name='Purify',
    school=School.HOLY,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.DISPEL, implicit_target_a=21, misc_value=3),
        Effect(type=EffectType.DISPEL, implicit_target_a=21, misc_value=4),
    ],
    spell_icon_id=300,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 8, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Purifies the friendly target, removing $s1 disease effect and $s2 poison effect.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 4096, 'SpellClassSet': 10, 'SpellLevel': 8, 'SpellVisualID_1': 312, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


# paladin-rework S1 (SHARED B5.7 / B9): 100 / 100, doubled vs Demons and Undead by spell_pal_holy_wrath; TargetCreatureType 36 -> 0 (all enemies); the stun (eff2) moves
# to helper 201141 (declared below); the spell has no aura left, so its duration / aura text go.
holy_wrath_2812 = spell(
    id=2812,
    name='Holy Wrath',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    category=35,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=30000,
    mana_cost=0,
    mana_cost_pct=20,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=100.0, ap_potency=100.0, potency_kind='direct', implicit_target_a=22, implicit_target_b=15, radius_yards=10.0),
    ],
    spell_icon_id=158,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 50); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. Potency system P7 (paladin pass): converted to sp_potency=125.0 / ap_potency=125.0 (paladin-potency-proposals.txt total 250.0, user value; was 244.5 from a stale worktree copy, corrected 2026-10-02; split evenly - matches the pre-existing 0.07/0.07 equal SP/AP coefficient split); also fixes PLAN F13 (zeroed direct_bonus restored as a side effect of the conversion).',
    raw_overrides={'AttributesEx': 136, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Sends bolts of holy power in all directions, causing {pot1*mult_hw} Holy damage to all enemies within $a1 yards, doubled against Demons and Undead, and stunning Demons and Undead for $201141d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'Speed': 20.0, 'SpellClassMask_2': 2097152, 'SpellClassSet': 10, 'SpellDescriptionVariableID': 1104, 'SpellLevel': 50, 'SpellPriority': 50, 'SpellVisualID_1': 126, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


cleanse_4987 = spell(
    id=4987,
    name='Cleanse',
    school=School.HOLY,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.DISPEL, implicit_target_a=21, misc_value=4),
        Effect(type=EffectType.DISPEL, implicit_target_a=21, misc_value=3),
        Effect(type=EffectType.DISPEL, implicit_target_a=21, misc_value=1),
    ],
    spell_icon_id=321,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 42, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Cleanses a friendly target, removing $s1 poison effect, $s2 disease effect, and $s3 magic effect.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 4096, 'SpellClassSet': 10, 'SpellLevel': 42, 'SpellVisualID_1': 337, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


hand_of_sacrifice_6940 = spell(
    id=6940,
    name='Hand of Sacrifice',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    category=1186,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=30.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=57, apply_aura=81, misc_value=127),
    ],
    spell_icon_id=504,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 655360, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Transfers $s1% damage taken to the paladin.', 'BaseLevel': 46, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Places a Hand on the party or raid member, transfering $s1% damage taken to the caster.  Lasts $d or until the caster has transfered $s2% of their maximum health.  Players may only have one Hand on them per Paladin at any one time.', 'EffectBasePoints_2': 99, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 699048, 'SpellClassMask_1': 8192, 'SpellClassSet': 10, 'SpellLevel': 46, 'SpellVisualID_1': 299, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


blessing_of_might_19740 = spell(
    id=19740,
    name='Blessing of Might',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=30.0,
    duration_ms=600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, points_per_level=6.973684210526316, implicit_target_a=21, apply_aura=AuraType.MOD_ATTACK_POWER),
        Effect(type=EffectType.APPLY_AURA, base_points=19, points_per_level=6.973684210526316, implicit_target_a=21, apply_aura=124),
    ],
    spell_icon_id=298,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 4); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 10 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases attack power by $s1.', 'BaseLevel': 4, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Places a Blessing on the friendly target, increasing attack power by $s1 for $d.  Players may only have one Blessing on them per Paladin at any one time.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 2, 'SpellClassSet': 10, 'SpellLevel': 4, 'SpellVisualID_1': 9179, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


blessing_of_wisdom_19742 = spell(
    id=19742,
    name='Blessing of Wisdom',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=30.0,
    duration_ms=600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, points_per_level=1.2424242424242424, implicit_target_a=21, apply_aura=85),
    ],
    spell_icon_id=306,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 14); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx3': 1, 'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Restores $s1 mana every 5 seconds.', 'BaseLevel': 14, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Places a Blessing on the friendly target, restoring $s1 mana every 5 seconds for $d.  Players may only have one Blessing on them per Paladin at any one time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 65536, 'SpellClassSet': 10, 'SpellLevel': 14, 'SpellVisualID_1': 5400, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


flash_of_light_19750 = spell(
    id=19750,
    name='Flash of Light',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, sp_potency=90.0, potency_kind='heal', implicit_target_a=21),
    ],
    spell_icon_id=242,
    tooltip_vars=holy_heal_tooltip,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. Potency system P7 (paladin pass): converted to sp_potency=90.0 (paladin-potency-proposals.txt, user value; was 52.7 from a stale worktree copy of the proposals file, corrected 2026-10-02). | paladin-rework S2 HOLY 4.1: sp_potency 75 -> 90 (953 at 60); description {pot1*hl} (entry 1105 owned by paladin_holy_spells.py).',
    raw_overrides={'AttributesEx6': 33554432, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals a friendly target for {pot1*hl}.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 1073741824, 'SpellClassSet': 10, 'SpellLevel': 20, 'SpellVisualID_1': 6623, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


divine_intervention_19752 = spell(
    id=19752,
    name='Divine Intervention',
    school=School.HOLY,
    attributes=537198592,
    cast_time_ms=0,
    cooldown_ms=600000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=40.0,
    effects=[
        Effect(type=79, base_points=-1, implicit_target_a=57),
        Effect(type=EffectType.TRIGGER_SPELL, base_points=-1, implicit_target_a=57, trigger_spell=19753),
        Effect(type=1, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=58,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 655360, 'AttributesEx2': 8, 'AttributesEx3': 256, 'AttributesEx4': 65792, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Complete immunity but unable to move.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "The paladin sacrifices $ghimself:herself; to remove the targeted party member from harm's way.  Enemies will stop attacking the protected party member, who will be immune to all harmful attacks but will not be able to take any action for $19753d.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ReagentCount_1': 1, 'Reagent_1': 17033, 'SpellClassSet': 10, 'SpellLevel': 30, 'SpellVisualID_1': 5402, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


# paladin-rework S1 (SHARED B1.1-B1.3 / B9 1102): 10 s seal, own cooldown, 1% mana, flat GCD (IS_ABILITY), StackAmount 10, eff1 = PROC_TRIGGER_SPELL -> auto-attack passive 201085,
# stale effects / masks stripped, learn level 6.
seal_of_light_20165 = spell(
    id=20165,
    name='Seal of Light',
    school=School.HOLY,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=1,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=201085),
    ],
    spell_icon_id=299,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Melee attacks deal Holy damage and may heal you.', 'BaseLevel': 6, 'CastingTimeIndex': 1, 'CumulativeAura': 10, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Fills you with divine light for $d.  Each melee hit deals ${5*$<mult_seal>}% weapon damage as Holy damage and has a 20% chance to heal you for 20% of your base health.  Crusader Strike and other seal builders add a stack (max 10).  When the seal expires it becomes Primed for 20 sec; Judgement and Deliverance unleash it.  Only one seal can be active at a time.\n\nUnleash: Heals you, increased by 10% per stack, and increases your Holy damage by 1.25% per stack for 15 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassMask_2': 33554432, 'SpellClassSet': 10, 'SpellDescriptionVariableID': 1102, 'SpellLevel': 6, 'SpellVisualID_1': 8073, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


# paladin-rework S1 (SHARED B1.1-B1.3 / B9 1102): 10 s seal, own cooldown, 1% mana, flat GCD (IS_ABILITY), StackAmount 10, eff1 = PROC_TRIGGER_SPELL -> auto-attack passive 201086,
# stale effects / masks stripped, learn level 10.
seal_of_wisdom_20166 = spell(
    id=20166,
    name='Seal of Wisdom',
    school=School.HOLY,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=1,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=201086),
    ],
    spell_icon_id=206,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Melee attacks deal Holy damage and may restore mana.', 'BaseLevel': 10, 'CastingTimeIndex': 1, 'CumulativeAura': 10, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Fills you with divine wisdom for $d.  Each melee hit deals ${5*$<mult_seal>}% weapon damage as Holy damage and has a 20% chance to restore 20% of your base mana.  Crusader Strike and other seal builders add a stack (max 10).  When the seal expires it becomes Primed for 20 sec; Judgement and Deliverance unleash it.  Only one seal can be active at a time.\n\nUnleash: Deals Holy and Arcane damage, increased by 10% per stack, and restores 10% of your maximum mana every sec for 5 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassMask_2': 67108864, 'SpellClassSet': 10, 'SpellDescriptionVariableID': 1102, 'SpellLevel': 10, 'SpellVisualID_1': 7987, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


blessing_of_kings_20217 = spell(
    id=20217,
    name='Blessing of Kings',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=30.0,
    duration_ms=600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=21, apply_aura=137, misc_value=-1),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=21, apply_aura=166),
    ],
    spell_icon_id=332,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases stats by $s1%.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Places a Blessing on the friendly target, increasing total stats by $s1% for $d.  Players may only have one Blessing on them per Paladin at any one time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 16777216, 'SpellClassSet': 10, 'SpellLevel': 20, 'SpellVisualID_1': 9187, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


charger_23214 = spell(
    id=23214,
    name='Charger',
    school=School.HOLY,
    mechanic=21,
    attributes=269844480,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=78, misc_value=14565),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=32),
        Effect(type=77, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=1716,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx3': 536870912, 'AttributesEx6': 131072, 'AttributesEx7': 512, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases speed by $s2%.', 'BaseLevel': 40, 'CastingTimeIndex': 16, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Charger, which serves as a mount.  This is a very fast mount.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Summon', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 268435456, 'SpellClassSet': 10, 'SpellLevel': 40, 'SpellVisualID_1': 3339},
)


# paladin-rework S1 (SHARED B5.9 / B9): 100 / 100 potency; tooltip multiplies by tooltip_vars 1104 `mult_how`.
hammer_of_wrath_24275 = spell(
    id=24275,
    name='Hammer of Wrath',
    school=School.HOLY,
    attributes=327680,
    category=1131,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=6000,
    mana_cost=0,
    mana_cost_pct=12,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=100.0, ap_potency=100.0, potency_kind='direct', implicit_target_a=6),
    ],
    spell_icon_id=42,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 44); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. Potency system P7 (paladin pass): converted to sp_potency=150.0 / ap_potency=150.0 (paladin-potency-proposals.txt total 300.0, user value; was 268.8 from a stale worktree copy, corrected 2026-10-02; split evenly - matches the pre-existing 0.15/0.15 equal SP/AP coefficient split); also fixes PLAN F13 (zeroed direct_bonus restored as a side effect of the conversion).',
    raw_overrides={'AttributesEx4': 512, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Hurls a hammer that strikes an enemy for {pot1*mult_how} Holy damage.  Only usable on enemies that have 20% or less health.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 50.0, 'SpellClassMask_2': 128, 'SpellClassSet': 10, 'SpellDescriptionVariableID': 1104, 'SpellLevel': 44, 'SpellVisualID_1': 7250, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetAuraState': 2},
)


blessing_of_wisdom_25290 = spell(
    id=25290,
    name='Blessing of Wisdom',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=30.0,
    duration_ms=600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=21, apply_aura=85),
    ],
    spell_icon_id=306,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid)',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx3': 1, 'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Restores $s1 mana every 5 seconds.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Places a Blessing on the friendly target, restoring $s1 mana every 5 seconds for $d.  Players may only have one Blessing on them per Paladin at any one time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 6', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 65536, 'SpellClassSet': 10, 'SpellLevel': 60, 'SpellVisualID_1': 5400, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


blessing_of_might_25291 = spell(
    id=25291,
    name='Blessing of Might',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=30.0,
    duration_ms=600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=231, implicit_target_a=21, apply_aura=AuraType.MOD_ATTACK_POWER),
        Effect(type=EffectType.APPLY_AURA, base_points=231, implicit_target_a=21, apply_aura=124),
    ],
    spell_icon_id=298,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid)',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases attack power by $s1.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Places a Blessing on the friendly target, increasing attack power by $s1 for $d.  Players may only have one Blessing on them per Paladin at any one time.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'MaxLevel': 60, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 7', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 2, 'SpellClassSet': 10, 'SpellLevel': 60, 'SpellVisualID_1': 9179, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


holy_light_25292 = spell(
    id=25292,
    name='Holy Light',
    school=School.HOLY,
    attributes=65536,
    cast_time_ms=2500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=29,
    range_yards=40.0,
    effects=[
        Effect(
            type=EffectType.HEAL, base_points=2033, points_per_level=5.800000190734863, die_sides=233, implicit_target_a=21,
            potency_excluded="superseded rank, kept only because an item_template row casts this exact "
            "spell id (see this spell's notes=) - potency forces MaxLevel=0 (uncapped) for the whole "
            "spell, which would silently remove this rank's historical MaxLevel=65 power ceiling. Same "
            "category as the Warlock pilot's Immolate Rank 3/8 exclusions (potency-system.PROGRESS.md "
            "P4); conservative default per P5/P7 - exclude, keep as-is.",
        ),
    ],
    spell_icon_id=70,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid). Potency system P7 (paladin pass): NOT converted - MaxLevel=65 is this rank\'s own historical power cap, and potency forces MaxLevel=0 spell-wide; conservative default (P4/P5 precedent) is to exclude and keep this rank exactly as-is rather than uncap it.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 20, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals a friendly target for $s1.', 'EffectBonusMultiplier_1': 1.6790000200271606, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 65, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 9', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 10, 'SpellLevel': 60, 'SpellVisualID_1': 2936, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


greater_blessing_of_might_25782 = spell(
    id=25782,
    name='Greater Blessing of Might',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=40.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=184, points_per_level=13.035714285714286, implicit_target_a=61, apply_aura=AuraType.MOD_ATTACK_POWER, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=184, points_per_level=13.035714285714286, implicit_target_a=61, apply_aura=124, radius_yards=100.0),
    ],
    spell_icon_id=1802,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 52); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases attack power by $s1.', 'BaseLevel': 52, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives all members of the raid or group that share the same class with the target the Greater Blessing of Might, increasing attack power by $s1 for $d.  Players may only have one Blessing on them per Paladin at any one time.', 'EffectBasePoints_3': -1, 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 0, 'Reagent_1': 0, 'SpellClassMask_1': 2, 'SpellClassSet': 10, 'SpellLevel': 52, 'SpellVisualID_1': 9179, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


greater_blessing_of_wisdom_25894 = spell(
    id=25894,
    name='Greater Blessing of Wisdom',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=11,
    range_yards=40.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, points_per_level=2.3846153846153846, implicit_target_a=61, apply_aura=85, radius_yards=100.0),
    ],
    spell_icon_id=1805,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 54); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 1024, 'AttributesEx3': 1, 'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Restores $s1 mana every 5 seconds.', 'BaseLevel': 54, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives all members of the raid or group that share the same class with the target the Greater Blessing of Wisdom, restoring $s1 mana every 5 seconds for $d.  Players may only have one Blessing on them per Paladin at any one time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 0, 'Reagent_1': 0, 'SpellClassMask_1': 65536, 'SpellClassSet': 10, 'SpellLevel': 54, 'SpellVisualID_1': 5400, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


redemption_7328 = spell(
    id=7328,
    name='Redemption',
    school=School.HOLY,
    attributes=268435456,
    cast_time_ms=10000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=64,
    range_yards=30.0,
    effects=[
        # Single-rank collapse (same recipe as Resurrection 2006 / bootstrap.py's top-rank anchor): rank 1's
        # BasePoints 64 at BaseLevel 12, slope = (rank 7's 1759 - 64) / (80 - 12) so a level-80 caster restores
        # 1760 health (what rank 7 / 48950 gave); MiscValue is the flat mana restored, rank 7's 1320.
        Effect(type=113, base_points=64, points_per_level=24.926470588235293, misc_value=1320),
    ],
    spell_icon_id=121,
    notes='single-rank collapse of Redemption 7328/10322/10324/20772/20773/48949/48950: rank 1 id kept as THE spell '
          '(learn level 12); health = 65 + 24.9265/level above 12 (1760 at level 80 = rank 7), mana 1320 = rank 7; '
          'MaxLevel 80; cast time / mana cost % identical across all ranks (10 s / 64%). Higher ranks are untrained '
          'and unranked below but stay in Spell.dbc untouched (characters may still know them).',
    raw_overrides={'AttributesEx': 131072, 'Targets': 32768, 'CastingTimeIndex': 7, 'InterruptFlags': 15, 'ProcChance': 101, 'BaseLevel': 12, 'SpellLevel': 12, 'MaxLevel': 80, 'DurationIndex': 0, 'EquippedItemClass': -1, 'SpellVisualID_1': 41, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Brings a dead player back to life with $s1 health and $q1 mana.  Cannot be cast when in combat.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0},
)
# Redemption ranks 2-7 are no longer taught or chained (the single-rank rollout missed the paladin chain).
untrain(10322, trainer_ids=[202])
untrain(10324, trainer_ids=[202])
untrain(20772, trainer_ids=[202])
untrain(20773, trainer_ids=[202])
unrank_spells(7328, 10322, 10324, 20772, 20773, 48949, 48950)


greater_blessing_of_kings_25898 = spell(
    id=25898,
    name='Greater Blessing of Kings',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=12,
    range_yards=40.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=61, apply_aura=137, misc_value=-1, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=61, apply_aura=166, radius_yards=100.0),
    ],
    spell_icon_id=1800,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases stats by $s1%.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives all members of the raid or group that share the same class with the target the Greater Blessing of Kings, increasing total stats by $s1% for $d.  Players may only have one Blessing on them per Paladin at any one time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 0, 'Reagent_1': 0, 'SpellClassMask_1': 16777216, 'SpellClassSet': 10, 'SpellLevel': 60, 'SpellVisualID_1': 9187, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


greater_blessing_of_sanctuary_25899 = spell(
    id=25899,
    name='Greater Blessing of Sanctuary',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=14,
    range_yards=40.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-4, implicit_target_a=61, apply_aura=AuraType.DUMMY, misc_value=127, radius_yards=100.0),
    ],
    spell_icon_id=1804,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage taken reduced by 3%, Strength and Stamina increased by $s2%, and blocked, parried or dodged melee attacks grant 6% of base mana.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives all members of the raid or group that share the same class with the target the Greater Blessing of Sanctuary, reducing damage taken from all sources by 3% for $d and increasing Strength and Stamina by $s2%. In addition, when the target blocks, parries or dodges a melee attack it gains 6% of its base mana.  Players may only have one Blessing on them per Paladin at any one time.', 'EffectBasePoints_2': 9, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 40, 'ReagentCount_1': 0, 'Reagent_1': 0, 'SpellClassMask_1': 268435456, 'SpellClassSet': 10, 'SpellLevel': 60, 'SpellVisualID_1': 7323, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


# paladin-rework S1 (SHARED B5.6 / B5.6a / C2.2d): snapshot pattern (Rain of Fire shape). eff1 is a DUMMY persistent-area source carrying the potency (10.13 / 10.12 per 1 s tick),
# eff2 a new unhasted 1 s PERIODIC_DUMMY tick driver; spell_pal_consecration casts the tick 201140 at the dynobj. Learn 6.
consecration_26573 = spell(
    id=26573,
    name='Consecration',
    school=School.HOLY,
    attributes=65536,
    category=932,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=8000,
    mana_cost=0,
    mana_cost_pct=22,
    range_yards=0.0,
    duration_ms=8000,
    effects=[
        Effect(
            type=EffectType.PERSISTENT_AREA_AURA, sp_potency=10.13, ap_potency=10.12, potency_kind='periodic',
            time_basis_ms=1000, implicit_target_a=18, implicit_target_b=16, apply_aura=AuraType.DUMMY, radius_yards=8.0,
        ),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=1000),
    ],
    spell_icon_id=51,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 8 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. '
    'Potency system P7 (paladin pass), PLAN F13 fix: this effect is a PERSISTENT_AREA_AURA whose own apply_aura is PERIODIC_DAMAGE - potency_report.py\'s classify_effect() only recognizes a bare APPLY_AURA+PERIODIC_DAMAGE shape, so this row never appeared in paladin-potency-report.md even though it is one of the six F13 "mixed" rows (data/sql/updates/db_world/2026_09_01_26.sql:445 zeroed its spell_bonus_data dot_bonus, same bug as Exorcism/Holy Wrath/Hammer of Wrath/Avenger\'s Shield/Holy Shield). Base-implied potency (from V60=77.3 at level 60) was 43.7 against the pre-bug coefficient-implied 14/14 - since this row never made it into paladin-potency-report.md for the user to review alongside the other five F13 spells, the user set it directly to an even 35/35 (70 total) rather than either derived value. Full potency conversion chosen over a narrower spell_bonus_data-only fix since the effect shape fully supports it (same mechanism as the other five, just a different effect type).',
    raw_overrides={'AttributesEx': 268435592, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Consecrates the land beneath you, dealing {pot1*mult_cons} Holy damage every sec for $d to enemies in the area.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 32, 'SpellClassSet': 10, 'SpellDescriptionVariableID': 1104, 'SpellLevel': 6, 'SpellPriority': 50, 'SpellVisualID_1': 5600, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


righteous_defense_31789 = spell(
    id=31789,
    name='Righteous Defense',
    school=School.HOLY,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=8000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=21, radius_yards=5.0),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=1, trigger_spell=31980),
    ],
    spell_icon_id=2037,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 524288, 'AttributesEx5': 2048, 'AttributesEx6': 8, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 14, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Come to the defense of a friendly target, commanding up to 3 enemies attacking the target to attack the Paladin instead.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 4, 'SpellClassSet': 10, 'SpellLevel': 14, 'SpellVisualID_1': 7893},
)
# Only on a stock TrainerId no NPC uses; 202 is the live Paladin trainer (docs/spell_learn_level.md).
trained_by(righteous_defense_31789, trainer_id=202, req_level=14, money_cost=2000)


# paladin-rework S1 (SHARED B1.1-B1.3 / B9 1102): 10 s seal, own cooldown, 1% mana, flat GCD (IS_ABILITY), StackAmount 10, eff1 = PROC_TRIGGER_SPELL -> auto-attack passive 201083,
# stale effects / masks stripped, learn level 20.
seal_of_vengeance_31801 = spell(
    id=31801,
    name='Seal of Vengeance',
    school=School.HOLY,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=1,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=201083),
    ],
    spell_icon_id=2292,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Melee attacks deal Holy damage.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'CumulativeAura': 10, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Fills you with holy power for $d.  Each melee hit deals ${10*$<mult_seal>}% weapon damage as Holy damage.  Crusader Strike and other seal builders add a stack (max 10).  When the seal expires it becomes Primed for 20 sec; Judgement and Deliverance unleash it.  Only one seal can be active at a time.\n\nUnleash: Afflicts the target with Twilight damage over 15 sec, increased by 10% per stack, and shields you for 20% of the damage it will deal.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassMask_2': 2048, 'SpellClassSet': 10, 'SpellDescriptionVariableID': 1102, 'SpellLevel': 20, 'SpellVisualID_1': 8062, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


# paladin-rework S1 (SHARED B5.5): learn 50, ExcludeCasterAuraSpell 61987 dropped (both lockout directions, data only), tooltip drops the lockout sentence.
avenging_wrath_31884 = spell(
    id=31884,
    name='Avenging Wrath',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=79, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=136, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=108, misc_value=11),
    ],
    spell_icon_id=2168,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'All damage and healing caused increased by $s1%.', 'BaseLevel': 50, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all damage and healing caused by $s1% for $d.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskC_2': 128, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712174, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 8192, 'SpellClassSet': 10, 'SpellLevel': 50, 'SpellVisualID_1': 7880},
)


summon_charger_34767 = spell(
    id=34767,
    name='Summon Charger',
    school=School.HOLY,
    mechanic=21,
    attributes=269844480,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=78, misc_value=20030),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=32),
        Effect(type=77, die_sides=0, implicit_target_a=1),
    ],
    spell_icon_id=1716,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx3': 536870912, 'AttributesEx6': 131072, 'AttributesEx7': 256, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases speed by $s2%.', 'BaseLevel': 40, 'CastingTimeIndex': 16, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Charger, which serves as a mount.  This is a very fast mount.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Summon', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 268435456, 'SpellClassSet': 10, 'SpellLevel': 40, 'SpellVisualID_1': 3339},
)


judgement_of_justice_53407 = spell(
    id=53407,
    name='Judgement of Justice',
    school=School.HOLY,
    attributes=327680,
    category=1210,
    cast_time_ms=0,
    cooldown_ms=10000,
    category_cooldown_ms=10000,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=10.0,
    effects=[
        Effect(type=77, base_points=-1, implicit_target_a=6),
    ],
    spell_icon_id=3013,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 1048576, 'AttributesEx3': 196608, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 28, 'CasterAuraState': 5, 'CastingTimeIndex': 1, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Unleashes the energy of a Seal spell to judge an enemy for $20184d, preventing them from fleeing and limiting their movement speed.  Refer to individual Seals for additional Judgement effect.  Only one Judgement per Paladin can be active at any one time.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'SpellClassMask_3': 8, 'SpellClassSet': 10, 'SpellLevel': 28, 'SpellVisualID_1': 11853, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


judgement_of_wisdom_53408 = spell(
    id=53408,
    name='Judgement of Wisdom',
    school=School.HOLY,
    attributes=327680,
    category=1210,
    cast_time_ms=0,
    cooldown_ms=10000,
    category_cooldown_ms=10000,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=10.0,
    effects=[
        Effect(type=77, base_points=-1, implicit_target_a=6),
    ],
    spell_icon_id=3014,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 1048576, 'AttributesEx3': 196608, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 12, 'CasterAuraState': 5, 'CastingTimeIndex': 1, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Unleashes the energy of a Seal spell to judge an enemy for $20186d, giving each attack a chance to restore $20268s1% of the attacker's base mana.  Refer to individual Seals for additional Judgement effect.  Only one Judgement per Paladin can be active at any one time.", 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'SpellClassMask_1': 8388608, 'SpellClassSet': 10, 'SpellLevel': 12, 'SpellVisualID_1': 11855, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


# paladin-rework S1 (SHARED C2.2e): learn 48 (potency spell: BaseLevel is generated from SpellLevel); 145.8 SP and the block-value term kept.
shield_of_righteousness_53600 = spell(
    id=53600,
    name='Shield of Righteousness',
    school=School.HOLY,
    attributes=327680,
    category=1209,
    cast_time_ms=0,
    cooldown_ms=6000,
    category_cooldown_ms=6000,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=145.8, potency_kind='direct', implicit_target_a=6, chain_targets=1),
    ],
    spell_icon_id=3031,
    tooltip_vars=prot_sor_tooltip,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 75); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 2 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. Potency system P7 (paladin pass): converted to sp_potency=145.8 (potency-report base-damage default; not mismatched - this flat bonus never had an SP coefficient at all live, so the new 0.625 coefficient is a real, intended gain from "move to the formula", docs/potency-system.md D4). Only this flat $s1 bonus effect is touched - the separate block-value-based effect (EffectBasePoints_2=99, not modeled by this Effect() list) is untouched.',
    raw_overrides={'AttributesEx': 512, 'AttributesEx4': 262144, 'AttributesEx6': 256, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Slam the target with your shield, causing Holy damage based on your block value plus an additional {pot1*il}.', 'EffectBasePoints_2': 99, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': 4, 'EquippedItemSubclass': 64, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 1048576, 'SpellClassSet': 10, 'SpellLevel': 48, 'SpellVisualID_1': 11792, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


# paladin-rework S1 (SHARED B5.11): learn 60; text stops quoting $58597s1 (cross-spell tokens do not level-scale; the absorb is potency now).
sacred_shield_53601 = spell(
    id=53601,
    name='Sacred Shield',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=12,
    range_yards=40.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=21, apply_aura=AuraType.DUMMY, misc_value=127, trigger_spell=58597),
    ],
    spell_icon_id=3033,
    notes='pulled from existing data | paladin-rework S2 HOLY 4.1: tooltip polish, absorb amount via pot_text(58597) (no talent multiplier); $58597s2% kept (Q13 default keeps eff1)',
    raw_overrides={'AttributesEx5': 32, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': "Each time the target takes damage they gain a Sacred Shield, absorbing " + pot_text(sacred_shield_58597) + " damage and increasing the paladin's chance to critically hit with Flash of Light by $58597s2%.   The target cannot gain this effect more than once every $s2 sec.", 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Each time the target takes damage they gain a Sacred Shield, absorbing " + pot_text(sacred_shield_58597) + " damage and increasing the paladin's chance to critically hit with Flash of Light by $58597s2% for up to $58597d.  They cannot gain this effect more than once every $s2 sec.  Lasts $d.  This spell cannot be on more than one target at any one time.", 'EffectBasePoints_2': 5, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 1081344, 'SpellClassMask_2': 524288, 'SpellClassSet': 10, 'SpellLevel': 60, 'SpellVisualID_1': 11956, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


seal_of_corruption_53736 = spell(
    id=53736,
    name='Seal of Corruption',
    school=School.HOLY,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=14,
    range_yards=0.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=240),
        Effect(type=EffectType.APPLY_AURA, base_points=53732, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2292,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AttributesEx7': 256, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Melee attacks cause Holy damage over $53742d.', 'BaseLevel': 66, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Fills the Paladin with holy power, causing attacks to apply Blood Corruption, which deals ${(0.013*$SPH+0.025*$AP)*5} additional Holy damage over $31803d.  Once stacked to $31803u times, each of the Paladins attacks also deals $53739s1% weapon damage as additional Holy damage.  Blood Corruption can stack up to $31803u times.  Only one Seal can be active on the Paladin at any one time.  Lasts $d.\r\n\r\nUnleashing this Seal's energy will deal ${1+0.22*$SPH+0.14*$AP} Holy damage to an enemy, increased by 10% for each application of Blood Corruption on the target.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 68, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassMask_2': 2048, 'SpellClassSet': 10, 'SpellLevel': 66, 'SpellVisualID_1': 8062, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


# paladin-rework S1 (SHARED B5.4): learn 40, 3% of max mana per 3 s tick (15% over 15 s), the -50% heal modifier (eff2) neutralized to DUMMY 0 with its mask cleared.
divine_plea_54428 = spell(
    id=54428,
    name='Divine Plea',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=21, amplitude=3000),
        Effect(type=EffectType.APPLY_AURA, base_points=0, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
    ],
    spell_icon_id=2821,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Gaining $o1% of total mana.', 'BaseLevel': 40, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You gain $o1% of your total mana over $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 2147500032, 'SpellClassMask_3': 1, 'SpellClassSet': 10, 'SpellLevel': 40, 'SpellPriority': 50, 'SpellVisualID_1': 11947, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


hand_of_reckoning_62124 = spell(
    id=62124,
    name='Hand of Reckoning',
    school=School.HOLY,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=8000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=30.0,
    duration_ms=3000,
    effects=[
        Effect(type=114, die_sides=0, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=AuraType.MOD_TAUNT),
    ],
    spell_icon_id=3722,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx2': 67108864, 'AttributesEx4': 2048, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Taunted.', 'BaseLevel': 16, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Taunts the target to attack you.  If the target is tauntable and not currently targeting you, causes ${1+0.5*$AP} Holy damage.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 1073741824, 'SpellClassSet': 10, 'SpellLevel': 16, 'SpellVisualID_1': 34},
)
# Only on a stock TrainerId no NPC uses; 202 is the live Paladin trainer (docs/spell_learn_level.md).
trained_by(hand_of_reckoning_62124, trainer_id=202, req_level=16, money_cost=3000)


holy_shock_20473 = spell(
    id=20473,
    name='Holy Shock',
    school=School.HOLY,
    attributes=327680,
    category=892,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=6000,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=20.0,
    effects=[
        Effect(type=EffectType.DUMMY, die_sides=0, implicit_target_a=25),
    ],
    spell_icon_id=156,
    tooltip_vars=holy_heal_tooltip,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 40); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80 | paladin-rework S2 HOLY 4.1: mana_cost_pct 18 -> 10, SpellLevel/BaseLevel 40 -> 30; description via pot_text(25912/25914, var="shock") (entry 1105 owned by paladin_holy_spells.py)',
    raw_overrides={'AttributesEx3': 196608, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 30, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Blasts the target with Holy energy, causing ' + pot_text(holy_shock_25912, var="shock") + ' Holy damage to an enemy, or ' + pot_text(holy_shock_25914, var="shock") + ' healing to an ally.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 161, 'SpellClassMask_1': 2097152, 'SpellClassSet': 10, 'SpellLevel': 30, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


holy_shield_20925 = spell(
    id=20925,
    name='Holy Shield',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    category=931,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=15000,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=51),
        Effect(type=EffectType.APPLY_AURA, sp_potency=35.0, ap_potency=35.0, potency_kind='direct', implicit_target_a=1, apply_aura=43),
        Effect(type=EffectType.APPLY_AURA, base_points=0, die_sides=0, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
    ],
    spell_icon_id=453,
    tooltip_vars=prot_holy_shield_tooltip,
    notes='paladin-rework S3 PROTECTION 4.1: category cooldown 15 s, SpellLevel 30, eff2 -> aura 87 misc 126 (Consecrated Shield carrier, amount 0), tooltip var 1136. pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 40); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 6 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. '
    'Potency system P7 (paladin pass), PLAN F13 fix: effect 2 (the "damage when blocked" proc) is an APPLY_AURA whose aura type is PROC_TRIGGER_DAMAGE (43), not one of the PERIODIC_DAMAGE/PERIODIC_HEAL/SCHOOL_ABSORB shapes potency_report.py\'s classify_effect() recognizes, so this row never appeared in paladin-potency-report.md even though it is one of the six F13 "mixed" rows (data/sql/updates/db_world/2026_09_01_26.sql:444 zeroed its spell_bonus_data direct_bonus, same bug as Exorcism/Holy Wrath/Hammer of Wrath/Avenger\'s Shield/Consecration). Coefficient-implied potency was 21.0 SP + 13.1 AP = 34.1 total against the base-implied 65.8 (V60=176 at level 60, T=1.5s) - since this row never made it into paladin-potency-report.md for the user to review alongside the other five F13 spells, the user set it directly to an even 35/35 (70 total) rather than either derived value. Full potency conversion chosen over a narrower spell_bonus_data-only fix since the effect shape fully supports it.',
    raw_overrides={'AttributesEx3': 2, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Block chance increased by $s1%.  {pot2} Holy damage dealt to attacker when blocked.  $n charges.', 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases chance to block by $s1% for $d and deals {pot2*ld} Holy damage for each attack blocked while active. Each block expends a charge. $n charges.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 4, 'EquippedItemSubclass': 64, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 8, 'ProcTypeMask': 680, 'RangeIndex': 1, 'SpellClassMask_2': 64, 'SpellClassSet': 10, 'SpellLevel': 30, 'SpellVisualID_1': 5620, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


avenger_s_shield_31935 = spell(
    id=31935,
    name="Avenger's Shield",
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    category=1158,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=30000,
    mana_cost=0,
    mana_cost_pct=26,
    range_yards=30.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=132.35, ap_potency=132.35, potency_kind='direct', implicit_target_a=6, chain_targets=3),
        Effect(type=EffectType.APPLY_AURA, base_points=-51, mechanic=Mechanic.SNARE, implicit_target_a=6, apply_aura=AuraType.MOD_DECREASE_SPEED, chain_targets=3),
    ],
    spell_icon_id=2172,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 50); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. Potency system P7 (paladin pass): converted to sp_potency=132.35 / ap_potency=132.35 (paladin-potency-proposals.txt total 264.7, split evenly - matches the pre-existing 0.07/0.07 equal SP/AP coefficient split); also fixes PLAN F13 (zeroed direct_bonus restored as a side effect of the conversion).',
    raw_overrides={'AttributesEx4': 262144, 'AttributesEx6': 256, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Dazed.', 'CastingTimeIndex': 1, 'DefenseType': 3, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Hurls a holy shield at the enemy, dealing {pot1} Holy damage, Dazing them and then jumping to additional nearby enemies.  Affects $x1 total targets.  Lasts $d. Grants 2 stacks of Bulwark.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 4, 'EquippedItemSubclass': 64, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 35.0, 'SpellClassMask_1': 16384, 'SpellClassSet': 10, 'SpellLevel': 40, 'SpellVisualID_1': 7886, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


# paladin-rework S1 (SHARED B5.3): baseline at 22 (talent row repurposed by Ret).
repentance_20066 = spell(
    id=20066,
    name='Repentance',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    mechanic=Mechanic.KNOCKOUT,
    attributes=1114112,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=9,
    range_yards=20.0,
    duration_ms=60000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
    ],
    spell_icon_id=316,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 262144, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Incapacitated.', 'AuraInterruptFlags': 2, 'BaseLevel': 22, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Puts the enemy target in a state of meditation, incapacitating them for up to $d, and removing the effect of Righteous Vengeance.  Any damage caused will awaken the target.  Usable against Demons, Dragonkin, Giants, Humanoids and Undead.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 4, 'SpellClassSet': 10, 'SpellLevel': 22, 'SpellVisualID_1': 5539, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetCreatureType': 118},
)


divine_favor_20216 = spell(
    id=20216,
    name='Divine Favor',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=168099840,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=104,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Critical effect chance of next Flash of Light, Holy Light, or Holy Shock spell increased by $s1%.', 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When activated, gives your next Flash of Light, Holy Light, or Holy Shock spell a $s1% critical effect chance.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 3223322624, 'EffectSpellClassMaskA_2': 65536, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 81920, 'RangeIndex': 1, 'SpellClassMask_2': 256, 'SpellClassSet': 10, 'SpellVisualID_1': 7424},
)


# paladin-rework S1 (SHARED B1.1-B1.3 / B9 1102): 10 s seal, own cooldown, 1% mana, flat GCD (IS_ABILITY), StackAmount 10, eff1 = PROC_TRIGGER_SPELL -> auto-attack passive 201082,
# stale effects / masks stripped, learn level 20.
seal_of_command_20375 = spell(
    id=20375,
    name='Seal of Command',
    school=School.HOLY,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=1,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=201082),
    ],
    spell_icon_id=561,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Melee attacks deal Holy damage and strike additional targets.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'CumulativeAura': 10, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Fills you with holy command for $d.  Each melee hit deals ${10*$<mult_command>}% weapon damage as Holy damage that also strikes up to 2 more enemies when the attack hits a single target.  Crusader Strike and other seal builders add a stack (max 10).  When the seal expires it becomes Primed for 20 sec; Judgement and Deliverance unleash it.  Only one seal can be active at a time.\n\nUnleash: Deals Holy and Fire damage, increased by 10% per stack, and reduces the damage done by the target by 0.63% per stack for 8 sec. Deliverance also deals the full Judgement damage to the main target and its 2 closest targets.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassMask_1': 33554432, 'SpellClassSet': 10, 'SpellDescriptionVariableID': 1102, 'SpellLevel': 20, 'SpellVisualID_1': 7992, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


blessing_of_sanctuary_20911 = spell(
    id=20911,
    name='Blessing of Sanctuary',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=30.0,
    duration_ms=1800000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-4, implicit_target_a=21, apply_aura=AuraType.DUMMY, misc_value=127),
    ],
    spell_icon_id=19,
    notes='pulled from existing data | paladin-rework S3 PROTECTION 4.1: duration 30 min, tooltips state 3% DR / 6% base mana (replacement script spell_pal_blessing_of_sanctuary_prot)',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage taken reduced by 3%, Strength and Stamina increased by $s2%, and blocked, parried or dodged melee attacks grant 6% of base mana.', 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Places a Blessing on the friendly target, reducing damage taken from all sources by 3% and increasing Strength and Stamina by $s2% for $d. In addition, when the target blocks, parries or dodges a melee attack it gains 6% of its base mana. Players may only have one Blessing on them per Paladin at any one time.', 'EffectBasePoints_2': 9, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 40, 'SpellClassMask_1': 268435456, 'SpellClassSet': 10, 'SpellLevel': 30, 'SpellVisualID_1': 7323, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


aura_mastery_31821 = spell(
    id=31821,
    name='Aura Mastery',
    school=School.NORMAL,
    attributes=150994960,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=108, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=108, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=108, misc_value=23),
    ],
    spell_icon_id=2136,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx6': 4096, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Concentration Aura provides immunity to Silence and Interrupt effects.\r\nEffectiveness of all other auras increased by $s1%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes your Concentration Aura to make all affected targets immune to Silence and Interrupt effects and improve the effect of all other auras by $s1%.  Lasts $d.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 67108936, 'EffectSpellClassMaskB_1': 67108864, 'EffectSpellClassMaskC_1': 67108864, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10, 'SpellVisualID_1': 13619},
)


divine_illumination_31842 = spell(
    id=31842,
    name='Divine Illumination',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=134545408,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=1, apply_aura=72, misc_value=126),
    ],
    spell_icon_id=2138,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Mana cost of all spells reduced by $s1%.', 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of all spells by $s1% for $d.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 1, 'EffectSpellClassMaskA_1': 2121728, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 2147500032, 'SpellClassSet': 10, 'SpellVisualID_1': 7878},
)


# paladin-rework S1 (SHARED B5.1 / B9): baseline at 1 (SLA 15493 AcquireMethod 2 auto-learns it), weapon potency 140 on eff2 (whole percent, no hand base points);
# tooltip multiplies by tooltip_vars 1103 `mult_cs` (declared in paladin_seal_spells.py).
crusader_strike_35395 = spell(
    id=35395,
    name='Crusader Strike',
    school=School.NORMAL,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=4000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=5.0,
    duration_ms=1,
    effects=[
        Effect(type=121, base_points=-1, implicit_target_a=6),
        Effect(type=31, weapon_potency=140, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2309,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268435968, 'AttributesEx6': 1024, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'An instant strike that causes ${$m2*$<mult_cs>}% weapon damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_2': 32768, 'SpellClassSet': 10, 'SpellDescriptionVariableID': 1103, 'SpellLevel': 1, 'SpellVisualID_1': 8316, 'StanceBarOrder': 4294967295, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


# paladin-rework S1 (RETRIBUTION §4.7): weapon potency 150 on eff3, eff1 DUMMY 109 -> 149 (unused, older tooltips), learn 40 (row 6 rebase). DBC MaxTargets 5 kept
# (the load correction's 4 is overridden by spell_pal_divine_storm_ret).
divine_storm_53385 = spell(
    id=53385,
    name='Divine Storm',
    school=School.NORMAL,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=10000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=12,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=149, implicit_target_a=1),
        Effect(type=EffectType.DUMMY, base_points=24, implicit_target_a=1),
        Effect(type=31, weapon_potency=150, implicit_target_a=22, implicit_target_b=15, radius_yards=8.0),
    ],
    spell_icon_id=3027,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 16, 'AttributesEx5': 32768, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'An instant weapon attack that causes $s3% of weapon damage to up to 5 enemies within $a3 yards.  The Divine Storm heals up to 3 injured party or raid members for a total of $s2% of the damage caused.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'MaxTargets': 5, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 131072, 'SpellClassSet': 10, 'SpellLevel': 40, 'SpellVisualID_1': 12006, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


beacon_of_light_53563 = spell(
    id=53563,
    name='Beacon of Light',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=537198592,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=35,
    range_yards=60.0,
    duration_ms=60000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=57, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=1500, trigger_spell=53651),
    ],
    spell_icon_id=3032,
    notes='pulled from existing data | paladin-rework S2 HOLY 4.1: SpellLevel/BaseLevel 60 -> 50',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx4': 524288, 'AttributesEx5': 544, 'AttributesEx6': 4, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Beacon of Light.', 'AuraInterruptFlags': 524288, 'BaseLevel': 50, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'The target becomes a Beacon of Light to all members of your party or raid within a 60 yard radius.  Any heals you cast on party or raid members will also heal the Beacon for $s1% of the amount healed.  Only one target can be the Beacon of Light at a time. Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 16777216, 'SpellClassSet': 10, 'SpellLevel': 50, 'SpellVisualID_1': 11876, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


hammer_of_the_righteous_53595 = spell(
    id=53595,
    name='Hammer of the Righteous',
    school=School.HOLY,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=6000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.NORMALIZED_WEAPON_DMG, base_points=-1, implicit_target_a=6, chain_targets=3),
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=75, implicit_target_a=6, chain_targets=3),
    ],
    spell_icon_id=3023,
    notes='pulled from existing data. paladin-rework S3 PROTECTION 4.1: eff0 NORMALIZED_WEAPON_DMG + eff1 WEAPON_PERCENT_DAMAGE weapon_potency 75 (Crusader Strike shape, both chain 3), no direct-damage effect left (stock main-hand DPS hardcode inert), stale effect-2/3 keys + MaxLevel 59 / BaseLevel 50 removed, SpellLevel 20 (generator sets BaseLevel/MaxLevel).',
    raw_overrides={'AttributesEx': 512, 'AttributesEx4': 262144, 'AttributesEx6': 256, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Hammer the current target and up to ${$x2-1} additional nearby targets, causing $s2% weapon damage as Holy damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemSubclass': 41105, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'Speed': 35.0, 'SpellClassMask_2': 262144, 'SpellClassSet': 10, 'SpellLevel': 20, 'SpellVisualID_1': 11927, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


divine_sacrifice_64205 = spell(
    id=64205,
    name='Divine Sacrifice',
    school=School.NORMAL,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=35, base_points=29, implicit_target_a=1, apply_aura=81, misc_value=127, radius_yards=30.0),
    ],
    spell_icon_id=3837,
    notes='pulled from existing data | paladin-rework S3 PROTECTION 4.1: stale EffectSpellClassMaskA_1 0x800 dropped (aura 81 ignores it; EffectBasePoints_2/_3 kept for the script), SpellLevel 50 (non-potency, consistency)',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx3': 67108864, 'AttributesEx7': 1073741824, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s1% of all damage taken by party members redirected to the Paladin.', 'AuraInterruptFlags': 4718592, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "$s1% of all damage taken by party members within $a1 yards is redirected to you, up to $s3% of your maximum health. Damage that reduces you below $s2% health breaks the effect. Every 5% of your maximum health redirected grants a stack of Bulwark. Lasts $d.", 'EffectBasePoints_2': 19, 'EffectBasePoints_3': 39, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectDieSides_3': 1, 'EffectMultipleValue_1': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 699048, 'RangeIndex': 1, 'SpellClassMask_3': 4, 'SpellClassSet': 10, 'SpellLevel': 50, 'SpellVisualID_1': 13597, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


# paladin-rework S1 (SHARED B1.1-B1.3 / B9 1102): 10 s seal, own cooldown, 1% mana, flat GCD (IS_ABILITY), StackAmount 10, eff1 = PROC_TRIGGER_SPELL -> auto-attack passive 201081,
# stale effects / masks stripped, learn level 1.
seal_of_righteousness_21084 = spell(
    id=21084,
    name='Seal of Righteousness',
    school=School.HOLY,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=1,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=201081),
    ],
    spell_icon_id=25,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 524288, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Melee attacks deal Holy damage.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'CumulativeAura': 10, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Fills you with holy spirit for $d.  Each melee hit deals ${20*$<mult_seal>}% weapon damage as Holy damage.  Crusader Strike and other seal builders add a stack (max 10).  When the seal expires it becomes Primed for 20 sec; Judgement and Deliverance unleash it.  Only one seal can be active at a time.\n\nUnleash: Deals Holy damage, increased by 10% per stack, and increases the haste of party members within 40 yards by 0.63% per stack for 10 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassMask_1': 134217728, 'SpellClassMask_2': 536870912, 'SpellClassSet': 10, 'SpellDescriptionVariableID': 1102, 'SpellLevel': 1, 'SpellVisualID_1': 7986, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


# paladin-rework S1 (SHARED B1.1-B1.3 / B9 1102): 10 s seal, own cooldown, 1% mana, flat GCD (IS_ABILITY), StackAmount 10, eff1 = PROC_TRIGGER_SPELL -> auto-attack passive 201084,
# stale effects / masks stripped, learn level 14.
seal_of_justice_20164 = spell(
    id=20164,
    name='Seal of Justice',
    school=School.HOLY,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=1,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=201084),
    ],
    spell_icon_id=307,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Melee attacks deal Holy damage and may stun.', 'BaseLevel': 14, 'CastingTimeIndex': 1, 'CumulativeAura': 10, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Fills you with the spirit of justice for $d.  Each melee hit deals ${10*$<mult_seal>}% weapon damage as Holy damage and has a 20% chance to stun a creature for 0.5 sec.  Crusader Strike and other seal builders add a stack (max 10).  When the seal expires it becomes Primed for 20 sec; Judgement and Deliverance unleash it.  Only one seal can be active at a time.\n\nUnleash: Deals Holy and Frost damage, increased by 10% per stack (doubled against controlled targets), and stuns the target for 5 sec (2 sec with Deliverance). Bosses are not stunned.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassMask_1': 134217728, 'SpellClassSet': 10, 'SpellDescriptionVariableID': 1102, 'SpellLevel': 14, 'SpellVisualID_1': 9504, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


# paladin-rework S1 (SHARED B5.10 / C2.1; RETRIBUTION §2.4): 8 s, DS bit d2 0x8000 added (keeps d0 0x400000), tooltip drops Divine Protection and the Avenging Wrath sentence.
divine_shield_642 = spell(
    id=642,
    name='Divine Shield',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    mechanic=29,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=300000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=0.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=39, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=39, misc_value=126),
    ],
    spell_icon_id=81,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 32768, 'AttributesEx2': 2097152, 'AttributesEx5': 4, 'AttributesEx7': 1048576, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Immune to all attacks and spells, but reduces all damage you deal by $s1%.', 'AuraInterruptFlags': 4718592, 'BaseLevel': 34, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Protects the paladin from all damage and spells for $d, but reduces all damage you deal by $s1%.  Once protected, the target cannot be targeted by Divine Shield or Hand of Protection again for $25771d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'ExcludeCasterAuraSpell': 61988, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 4194304, 'SpellClassMask_3': 32768, 'SpellClassSet': 10, 'SpellLevel': 34, 'SpellVisualID_1': 154, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


# =====================================================================================================
# paladin-rework S1 (Retribution pass) - WP-A1: castables and the class-wide baseline.
# Specs: SHARED Part A / B (B1.1-B1.3 seals, B3 Judgement / Deliverance, B3.4 old castables, B5 baseline,
# B7 unbinds, B11) / C (C2 Forbearance sources, spell_category), RETRIBUTION §4.1 / 4.3 / 4.4 / 4.7 / 5.2.
# Everything below this banner is new; the edits to existing spells sit in their own blocks above.
# Cross-file references to spells another WP-A agent declares (passives 201081-201092, unleashes,
# tooltip_vars entries 1100-1104 / 1120-1122) are bare ids, never imports.
# =====================================================================================================


def _effect_mask(letter: str, mask: tuple[int, int, int]) -> dict:
    """`EffectSpellClassMask<letter>_<n>` raw keys for a (d0, d1, d2) composite. The LETTER is the effect
    index (A = Effect_1, B = Effect_2, C = Effect_3), the number the SpellFamilyFlags dword."""
    return {f'EffectSpellClassMask{letter}_{i}': v for i, v in enumerate(mask, start=1) if v}


def _raw(castable: bool = False, **extra) -> dict:
    """Common raw_overrides for a new paladin spell (RETRIBUTION §4 'Common'): family 10, no equipped item,
    MAGIC defense class (spell hit / crit), all-language masks, empty NameSubtext. Castables add the GCD
    (hasted, category 133), silence prevention and facing."""
    raw = {
        'AuraDescription_Lang_Mask': 16712188,
        'CastingTimeIndex': 1,
        'DefenseType': 1,
        'Description_Lang_Mask': 16712190,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': -1,
        'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': '',
        'Name_Lang_Mask': 16712190,
        'ProcChance': 101,
        'SpellClassSet': 10,
    }
    if castable:
        raw.update({'FacingCasterFlags': 1, 'PreventionType': 1, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500})
    raw.update(extra)
    return raw


# --- Judgement 201060 / Deliverance 201061 (SHARED B3.1) ---------------------------------------------
# Speed 0 (required: the dispatcher's AfterCast must run after the hits). Shared 6 s cooldown through
# stock category 1210 (free once the old castables are gone). Learn 4 / 20, SLA 30500 / 30501.
# No SUPPRESS_*_PROCS (stock 20271 had AttributesEx3 0x30000): Judgement-keyed talent rows must see these hits.
# Tooltips multiply by tooltip_vars 1100 (`mult_j` / `mult_dv`, SHARED B9), declared in paladin_seal_spells.py.
judgement_201060 = spell(
    id=201060,
    name='Judgement',
    school=School.HOLY,
    attributes=327680,
    category=1210,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=6000,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=10.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=50.0, ap_potency=50.0, potency_kind='direct', implicit_target_a=6),
    ],
    spell_icon_id=205,
    notes='paladin-rework S1 SHARED B3.1: own hit 100 potency hybrid (50 SP / 50 AP), MAGIC class, family bit J (d2 0x8), shared 6 s cooldown with Deliverance, castable with no Primed aura (D1). '
          'Visual copied from stock Judgement of Light 20271 (5651). spell_pal_judgement_dispatch does the Primed consume / unleash.',
    raw_overrides=_raw(
        castable=True,
        SpellClassMask_3=m.JUDGEMENT,
        SpellLevel=4,
        SpellVisualID_1=5651,
        SpellDescriptionVariableID=1100,
        Description_Lang_enUS='Judges an enemy, dealing {pot1*mult_j} Holy damage.  If a seal is Primed, also unleashes it on the target, +10% per seal stack.  Shares a cooldown with Deliverance.',
    ),
)
scripted_by(judgement_201060, 'spell_pal_judgement_dispatch')
skill_line_ability(id=30500, skill_line=184, spell_id=201060, class_mask=2)
trained_by(judgement_201060, trainer_id=202, req_level=4, money_cost=100)
trained_by(judgement_201060, trainer_id=203, req_level=4, money_cost=100)


deliverance_201061 = spell(
    id=201061,
    name='Deliverance',
    school=School.HOLY,
    attributes=327680,
    category=1210,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=6000,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=10.0,
    effects=[
        Effect(
            type=EffectType.SCHOOL_DAMAGE, sp_potency=20.0, ap_potency=20.0, potency_kind='direct',
            implicit_target_a=53, implicit_target_b=16, radius_yards=8.0,
        ),
    ],
    spell_icon_id=90181,
    notes='paladin-rework S1 SHARED B3.1: own hit 40 potency per target (20 SP / 20 AP) on the target + up to 4 enemies within 8 yd (MaxTargets 0, the dispatcher trims to 5), family bit Dv (d2 0x10000), '
          'shares the 6 s Judgement category. Icon 90181 = alias of the stock blue Judgement texture (build_patch_i.py).',
    raw_overrides=_raw(
        castable=True,
        SpellClassMask_3=m.DELIVERANCE,
        SpellLevel=20,
        SpellVisualID_1=5651,
        SpellDescriptionVariableID=1100,
        Description_Lang_enUS='Strikes the target and up to 4 other enemies within $a1 yards for {pot1*mult_dv} Holy damage each.  If a seal is Primed, also unleashes it on every target at 40% effect; effects on you happen once, at full value.  Shares a cooldown with Judgement.',
    ),
)
scripted_by(deliverance_201061, 'spell_pal_judgement_dispatch')
skill_line_ability(id=30501, skill_line=184, spell_id=201061, class_mask=2)
trained_by(deliverance_201061, trainer_id=202, req_level=20, money_cost=4000)
trained_by(deliverance_201061, trainer_id=203, req_level=20, money_cost=4000)


# --- Consecration tick 201140 / Holy Wrath stun 201141 (SHARED B5.6a / B5.7) ------------------------
consecration_tick_201140 = spell(
    id=201140,
    name='Consecration',
    school=School.HOLY,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(
            type=EffectType.SCHOOL_DAMAGE, implicit_target_a=87, implicit_target_b=16, radius_yards=8.0,
            potency_excluded='script-supplied snapshot bp (spell_pal_consecration passes SPELLVALUE_BASE_POINT0, Rain of Fire C5 pattern)',
        ),
    ],
    spell_icon_id=51,
    notes='paladin-rework S1 SHARED B5.6a: snapshot tick cast at the dynobj each second. Dest target -> range 50000 (CR1). IGNORE_CASTER_MODIFIERS (AttributesEx3 0x20000000, taken mods stay live). '
          'DefenseType MAGIC so it can crit (a direct cast, not a periodic aura). Shares Consecration d0 0x20; MaxTargets 0 = uncapped. SpellLevel 6 (Part C errata, cosmetic).',
    raw_overrides=_raw(
        AttributesEx2=0x4,  # SPELL_ATTR2_IGNORE_LINE_OF_SIGHT: script-cast at a target / dest the paladin may not see
        AttributesEx3=0x20000000,
        SpellClassMask_1=m.CONSECRATION,
        SpellLevel=6,
    ),
)


holy_wrath_stun_201141 = spell(
    id=201141,
    name='Holy Wrath',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=3000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, mechanic=Mechanic.STUN, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
    ],
    spell_icon_id=158,
    notes='paladin-rework S1 SHARED B5.7: the Demon / Undead stun moved out of Holy Wrath 2812 (a per-effect target filter cannot be relied on when both effects share identical targeting); '
          'spell_pal_holy_wrath casts it per Demon / Undead target. TargetCreatureType 36 kept as a safety net. No family bits.',
    raw_overrides=_raw(
        AttributesEx2=0x4,  # SPELL_ATTR2_IGNORE_LINE_OF_SIGHT: script-cast at a target / dest the paladin may not see
        AuraDescription_Lang_Mask=16712190,
        AuraDescription_Lang_enUS='Stunned.',
        SpellLevel=50,
        TargetCreatureType=36,
    ),
)


# --- Blade of Justice 201400 (RETRIBUTION §4.1) -----------------------------------------------------
# Talent-taught (row 1441, A3 declares the talent + SLA 30530). tooltip_vars 1120 `mult` (RETRIBUTION §5.3).
blade_of_justice_201400 = spell(
    id=201400,
    name='Blade of Justice',
    school=School.HOLY,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=10000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=4,
    range_yards=20.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=100.0, ap_potency=100.0, potency_kind='direct', implicit_target_a=6),
    ],
    spell_icon_id=90210,
    notes='paladin-rework S1 RETRIBUTION §4.1: 100 / 100 potency, 10 s cooldown (< 30 s: no Cooldown Haste), BoJ bit d2 0x800, learn 30. Visual = Crusader Strike SV 8316 placeholder (VFX follow-up). '
          'The six seal echoes 201401-201409 are paladin_trigger_spells.py.',
    raw_overrides=_raw(
        castable=True,
        SpellClassMask_3=m.BLADE_OF_JUSTICE,
        SpellLevel=30,
        SpellVisualID_1=8316,
        SpellDescriptionVariableID=1120,
        Description_Lang_enUS="Pierces an enemy with a blade of light, dealing {pot1*mult} Holy damage and releasing your active seal's effect at 300% strength, with any chance-based part guaranteed.  Grants 1 seal stack.",
    ),
)
scripted_by(blade_of_justice_201400, 'spell_pal_blade_of_justice', 'spell_pal_seal_builder')


# --- Execution Sentence 201410 + burst 201411 + splash 201412 (RETRIBUTION §4.3) ---------------------
# 201411 / 201412 first: 201410's tooltip quotes their potency through pot_text(). Entry 1121 holds `mult`
# (direct strikes) and `dot` (the DoT, which reads SPELLMOD_DOT). All three carry the ES bit d2 0x2000.
execution_sentence_burst_201411 = spell(
    id=201411,
    name='Execution Sentence',
    school=School.HOLY,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=180.0, ap_potency=180.0, potency_kind='direct', implicit_target_a=6),
    ],
    spell_icon_id=90212,
    notes='paladin-rework S1 RETRIBUTION §4.3: the hammer\'s main-target strike, 180 / 180, triggered only. Range 50000 (the hammer can expire with the paladin far away). '
          'spell_pal_execution_sentence_burst applies x(1 + 0.05 * gained) and keeps the main target out of the splash.',
    raw_overrides=_raw(
        AttributesEx2=0x4,  # SPELL_ATTR2_IGNORE_LINE_OF_SIGHT: script-cast at a target / dest the paladin may not see
        SpellClassMask_3=m.EXECUTION_SENTENCE,
        SpellLevel=50,
        SpellDescriptionVariableID=1121,
        Description_Lang_enUS='Deals {pot1*mult} Holy damage.',
    ),
)
scripted_by(execution_sentence_burst_201411, 'spell_pal_execution_sentence_burst')


execution_sentence_splash_201412 = spell(
    id=201412,
    name='Execution Sentence',
    school=School.HOLY,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(
            type=EffectType.SCHOOL_DAMAGE, sp_potency=90.0, ap_potency=90.0, potency_kind='direct',
            implicit_target_a=87, implicit_target_b=16, radius_yards=5.0,
        ),
    ],
    spell_icon_id=90212,
    notes='paladin-rework S1 RETRIBUTION §4.3: splash around the target / corpse, 90 / 90, 5 yd, MaxTargets 4 (starting value: the main target plus 4 = "burst up to 5"). Triggered only.',
    raw_overrides=_raw(
        AttributesEx2=0x4,  # SPELL_ATTR2_IGNORE_LINE_OF_SIGHT: script-cast at a target / dest the paladin may not see
        MaxTargets=4,
        SpellClassMask_3=m.EXECUTION_SENTENCE,
        SpellLevel=50,
        SpellDescriptionVariableID=1121,
        Description_Lang_enUS='Deals {pot1*mult} Holy damage to nearby enemies.',
    ),
)
scripted_by(execution_sentence_splash_201412, 'spell_pal_execution_sentence_burst')


execution_sentence_201410 = spell(
    id=201410,
    name='Execution Sentence',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=30.0,
    duration_ms=10000,
    effects=[
        Effect(
            type=EffectType.APPLY_AURA, sp_potency=36.0, ap_potency=36.0, potency_kind='periodic', implicit_target_a=6,
            apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=1000,
        ),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.MOD_DAMAGE_FROM_CASTER),
    ],
    spell_icon_id=90212,
    notes='paladin-rework S1 RETRIBUTION §4.3: DoT 36 / 36 per 1 s tick for 10 s (480 total at T 1 s), 60 s cooldown (>= 30 s: Cooldown Haste applies), magic-dispellable (a dispel fires the burst), ES bit d2 0x2000, learn 50. '
          'eff2 = aura 271 (damage taken from the caster) 0% until Fanaticism adds to it through SPELLMOD_EFFECT2; it reads SEAL_DAMAGE (U | P) on mask B. Visual = Hammer of Wrath SV 7250 placeholder (VFX follow-up).',
    raw_overrides=_raw(
        castable=True,
        AuraDescription_Lang_Mask=16712190,
        AuraDescription_Lang_enUS='Taking {pot1} Holy damage every $t1 sec.',
        SpellClassMask_3=m.EXECUTION_SENTENCE,
        SpellLevel=50,
        SpellVisualID_1=7250,
        SpellDescriptionVariableID=1121,
        Description_Lang_enUS=(
            'A hammer slowly falls upon the target, dealing {pot1.total*dot} Holy damage over $d.  When the hammer expires, is dispelled or the target becomes immune, it strikes the target for '
            + pot_text(execution_sentence_burst_201411, var='mult')
            + ' Holy damage and up to 4 other enemies within $201412a1 yards for '
            + pot_text(execution_sentence_splash_201412, var='mult')
            + ' Holy damage.  The final strike deals 5% more damage for each seal stack you gain while the hammer falls.  If the target dies first, only the strike around it occurs.'
        ),
        **_effect_mask('B', m.SEAL_DAMAGE),
    ),
)
scripted_by(execution_sentence_201410, 'spell_pal_execution_sentence')


# --- Wake of Ashes 201413 + stun 201414 (RETRIBUTION §4.4) ------------------------------------------
# Cone angle 104 deg is the engine's hard-coded value for TARGET_UNIT_CONE_ENEMY_104 with no spell_cone row (F10);
# more than 5 enemies in the cone -> a random 5 (engine RandomResize). tooltip_vars 1122 `mult`.
wake_of_ashes_201413 = spell(
    id=201413,
    name='Wake of Ashes',
    school=School.HOLY,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=45000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=RANGE_SELF,
    effects=[
        Effect(
            type=EffectType.SCHOOL_DAMAGE, sp_potency=205.0, ap_potency=205.0, potency_kind='direct',
            implicit_target_a=104, radius_yards=12.0,
        ),
    ],
    spell_icon_id=90211,
    notes='paladin-rework S1 RETRIBUTION §4.4: 205 / 205 potency in a 12 yd 104 degree cone, up to 5 targets, 45 s cooldown (Cooldown Haste applies), WoA bit d2 0x1000, learn 60. '
          'Visual = Divine Storm SV 12006 placeholder (VFX follow-up). Stun 201414 and the +3 seal stacks come from spell_pal_wake_of_ashes / the builder script.',
    raw_overrides=_raw(
        castable=True,
        MaxTargets=5,
        SpellClassMask_3=m.WAKE_OF_ASHES,
        SpellLevel=60,
        SpellVisualID_1=12006,
        SpellDescriptionVariableID=1122,
        Description_Lang_enUS='Lash out with the Light, dealing {pot1*mult} Holy damage to up to 5 enemies in a cone in front of you and stunning Demons and Undead for $201414d.  Grants 3 seal stacks.',
    ),
)
scripted_by(wake_of_ashes_201413, 'spell_pal_wake_of_ashes', 'spell_pal_seal_builder')


wake_of_ashes_stun_201414 = spell(
    id=201414,
    name='Wake of Ashes',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    mechanic=Mechanic.STUN,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, mechanic=Mechanic.STUN, implicit_target_a=6, apply_aura=AuraType.MOD_STUN),
    ],
    spell_icon_id=90211,
    notes='paladin-rework S1 RETRIBUTION §4.4: 5 s stun on Demons / Undead, cast by spell_pal_wake_of_ashes. Triggered only, no family bits.',
    raw_overrides=_raw(
        AttributesEx2=0x4,  # SPELL_ATTR2_IGNORE_LINE_OF_SIGHT: script-cast at a target / dest the paladin may not see
        AuraDescription_Lang_Mask=16712190,
        AuraDescription_Lang_enUS='Stunned.',
        SpellLevel=60,
    ),
)


# --- Trainer rows (SHARED B1.1 / B5 / C2.2; trainer 203 = the starter-zone trainer, B1.1) ------------
# Seals: prices are starting guesses (neighbouring rows). 203 teaches at the same level and price as 202.
for _trainer in (202, 203):
    trained_by(seal_of_command_20375, trainer_id=_trainer, req_level=20, money_cost=4000)
    trained_by(seal_of_justice_20164, trainer_id=_trainer, req_level=14, money_cost=2000)
    trained_by(seal_of_light_20165, trainer_id=_trainer, req_level=6, money_cost=100)
    trained_by(seal_of_wisdom_20166, trainer_id=_trainer, req_level=10, money_cost=300)
    trained_by(consecration_26573, trainer_id=_trainer, req_level=6, money_cost=100)  # C2.2d: learn 20 -> 6
trained_by(repentance_20066, trainer_id=202, req_level=22, money_cost=4000)  # B5.3 (talent row repurposed by Ret)
trained_by(divine_plea_54428, trainer_id=202, req_level=40, money_cost=20000)  # B5.4 (none existed)
trained_by(avenging_wrath_31884, trainer_id=202, req_level=50, money_cost=28000)  # B5.5 (none existed)
trained_by(sacred_shield_53601, trainer_id=202, req_level=60, money_cost=46000)  # B5.11 (none existed)
trained_by(shield_of_righteousness_53600, trainer_id=202, req_level=48, money_cost=26000)  # C2.2e (none live)
# B5.13: the Greater Blessings' dead ReqAbility (ranks removed by the single-rank migration) is dropped by re-declaring without it.
trained_by(greater_blessing_of_might_25782, trainer_id=202, req_level=52, money_cost=46000)
trained_by(greater_blessing_of_wisdom_25894, trainer_id=202, req_level=54, money_cost=46000)
# ...but the client-visible lock came from `spell_required` (Trainer::GetSpellState's "additional spell requirement"),
# a separate table: 25782 <- 19838 (Blessing of Might r6), 25894 <- 19854 (Blessing of Wisdom r5), both retired ranks.
unrequire_spell(greater_blessing_of_might_25782, 19838)
unrequire_spell(greater_blessing_of_wisdom_25894, 19854)

# B3.4: the old castable Judgements are no longer taught (their spell rows stay declared above).
untrain(20271, trainer_ids=[202, 203])
untrain(judgement_of_justice_53407, trainer_ids=[202])
untrain(judgement_of_wisdom_53408, trainer_ids=[202])


# --- SkillLineAbility edits to stock rows (SHARED B1.1 / B1.3 / B5.1) -------------------------------
skill_line_ability(id=11616, skill_line=184, spell_id=20375, class_mask=2)  # Seal of Command: ClassMask 0 -> 2 (baseline)
skill_line_ability(id=14779, skill_line=184, spell_id=31801, class_mask=2, race_mask=0)  # Seal of Vengeance: RaceMask 1029 -> 0 (both factions)
skill_line_ability(
    id=15493, skill_line=184, spell_id=35395, class_mask=2, raw_overrides={'AcquireMethod': 2},
)  # Crusader Strike: auto-learned at login (Player::learnSkillRewardedSpells), no trainer row


# --- Script bindings (SHARED B1.6 / B2.3 / B5 / B7, RETRIBUTION §5.2) --------------------------------
# Stock bindings the new classes displace. The real ScriptNames are used (spell_script_names rows),
# not the C++ class names: spell_pal_judgement is registered as the three *_of_<seal> names.
unbind_script(20154, 'spell_pal_seal_of_righteousness')  # superseded rank, retired (B1.1)
unbind_script(seal_of_righteousness_21084, 'spell_pal_seal_of_righteousness')
unbind_script(seal_of_command_20375, 'spell_pal_seal_of_command')  # 20424's own spell_pal_seal_of_command_aura binding stays (inert)
unbind_script(seal_of_light_20165, 'spell_pal_seal_of_light')
unbind_script(seal_of_wisdom_20166, 'spell_pal_seal_of_light')
unbind_script(seal_of_vengeance_31801, 'spell_pal_seal_of_vengeance')
unbind_script(seal_of_corruption_53736, 'spell_pal_seal_of_corruption')  # retired, spell row untouched (B1.3)
unbind_script(20271, 'spell_pal_judgement_of_light')
unbind_script(judgement_of_justice_53407, 'spell_pal_judgement_of_justice')
unbind_script(judgement_of_wisdom_53408, 'spell_pal_judgement_of_wisdom')
for _seal in (
    seal_of_righteousness_21084, seal_of_command_20375, seal_of_vengeance_31801,
    seal_of_justice_20164, seal_of_light_20165, seal_of_wisdom_20166,
):
    scripted_by(_seal, 'spell_pal_seal_aura')
scripted_by(seal_of_justice_20164, 'spell_pal_pursuit_of_justice_seal')  # RETRIBUTION §5.2
scripted_by(hand_of_freedom_1044, 'spell_pal_pursuit_of_justice_freedom')  # RETRIBUTION §5.2

# Seal builders (B2.3): Ret adds 201400 / 201413 above; Holy Shock's binding coexists with the stock -20473 row.
for _builder in (
    crusader_strike_35395, divine_storm_53385, exorcism_879, hammer_of_wrath_24275, consecration_26573,
    holy_wrath_2812, avenger_s_shield_31935, hammer_of_the_righteous_53595, holy_shock_20473,
):
    scripted_by(_builder, 'spell_pal_seal_builder')
scripted_by(crusader_strike_35395, 'spell_pal_crusader_strike_ret')
unbind_script(divine_storm_53385, 'spell_pal_divine_storm')
scripted_by(divine_storm_53385, 'spell_pal_divine_storm_ret')
scripted_by(consecration_26573, 'spell_pal_consecration')
scripted_by(holy_wrath_2812, 'spell_pal_holy_wrath')

# --- Protection (S3 PROTECTION 2.7 / 5.2): scripted_by / unbind_script ---------------------------------
scripted_by(avenger_s_shield_31935, 'spell_pal_avengers_shield_prot')  # beside spell_pal_seal_builder above
scripted_by(635, 'spell_pal_holy_light_bulwark')  # Holy Light: declared elsewhere, no stock binding, no data change here
scripted_by(divine_protection_498, 'spell_pal_divine_protection_prot')
unbind_script(divine_sacrifice_64205, 'spell_pal_divine_sacrifice')
scripted_by(divine_sacrifice_64205, 'spell_pal_divine_sacrifice_prot')
for _sanctuary in (blessing_of_sanctuary_20911, greater_blessing_of_sanctuary_25899):
    unbind_script(_sanctuary, 'spell_pal_blessing_of_sanctuary')  # spell_gen_damage_reduction_aura stays bound
    scripted_by(_sanctuary, 'spell_pal_blessing_of_sanctuary_prot')
scripted_by(consecration_tick_201140, 'spell_pal_improved_consecration_slow')
for _command_unleash in (201070, 201076):  # declared in paladin_seal_spells.py; bound there to spell_pal_seal_unleash
    scripted_by(_command_unleash, 'spell_pal_improved_soc_dot')

# Holy Shock (S2 HOLY 4.1): stock spell_pal_holy_shock replaced by the fork class; S1's spell_pal_seal_builder binding above stays.
unbind_script(-20473, 'spell_pal_holy_shock')
scripted_by(20473, 'spell_pal_holy_shock_holy')

# Sacred Shield (B5.11): the absorb spell 58597 is declared in paladin_trigger_spells.py (data edit is not this file's);
# the stock 75%-healing-power literal script is replaced by spell_pal_sacred_shield_absorb. 53601's own stock class stays.
unbind_script(58597, 'spell_pal_sacred_shield')
scripted_by(58597, 'spell_pal_sacred_shield_absorb')

# Part C (C2.1): Divine Protection no longer causes / checks Forbearance (spell_pal_immunities stays on 642 / -1022);
# Lay on Hands gets a fork copy of the stock class without the Forbearance ids. The negative id is the stock
# "this spell and every rank" convention the spec names (single-rank on this fork).
unbind_script(divine_protection_498, 'spell_pal_immunities')
unbind_script(-633, 'spell_pal_lay_on_hands')
scripted_by(-633, 'spell_pal_lay_on_hands_fork')

# Avenging Wrath: the stock rider (57318 on any Sanctified Wrath EFFECT_2) would fire for the reworked talent (RETRIBUTION §0.2 item 9).
unbind_script(avenging_wrath_31884, 'spell_pal_avenging_wrath')
linked_spell(-31884, -201431, comment='Crusade ramp 201431 (RETRIBUTION §4.6) ends with Avenging Wrath')


# --- spell_proc rows (SHARED B1.6 / B7 / B11) ---------------------------------------------------------
# The six seals: re-declared over the stock rows (stock had PPM 5/10/12 on Justice / Light / Wisdom and attr 2 on
# Righteousness / Vengeance). Auto attacks and seal-builder hits that landed (HIT phase), 100%; spell_pal_seal_aura's
# CheckProc filters the sources. The 20% chance auras 201093-201095 are paladin_seal_spells.py's.
for _seal in (
    seal_of_righteousness_21084, seal_of_command_20375, seal_of_vengeance_31801,
    seal_of_justice_20164, seal_of_light_20165, seal_of_wisdom_20166,
):
    procs_on(
        _seal, proc_flags=m.SEAL_PROC_FLAGS, spell_type_mask=m.PROC_SPELL_TYPE_DAMAGE,
        spell_phase_mask=m.PROC_SPELL_PHASE_HIT, chance=100.0,
    )

# B11: Judgement of Light / Wisdom debuffs (20185 / 20186, declared nowhere; bare ids). Same row as stock but ppm 0 /
# chance 100 so the fork's Proc Chance multiplier cannot shorten the real PPM-15 roll, which
# spell_pal_judgement_debuff_proc_rate re-runs in CheckProc. The stock classes (..._of_light_heal / ..._wisdom_mana) stay bound.
procs_on(20185, proc_flags=0, spell_type_mask=m.PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=0, chance=100.0)
procs_on(20186, proc_flags=0, spell_type_mask=m.PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=0, chance=100.0)
scripted_by(20185, 'spell_pal_judgement_debuff_proc_rate')
scripted_by(20186, 'spell_pal_judgement_debuff_proc_rate')


# --- Part C: the aura buttons' shared 15 s category (C1.2) ---------------------------------------------
# The five aura spells (465 / 7294 / 19746 / 19876 / 32223) are declared in paladin_trigger_spells.py and carry
# category=1300 / category_cooldown_ms=15000 / RecoveryTime 60000 there. Without this row SpellInfo::GetCategory()
# is silently 0 and the shared lock never exists (generate.py errors on a spell using an undeclared custom category).
spell_category(1300, flags=0, comment='paladin aura shared cooldown (SHARED Part C)')
